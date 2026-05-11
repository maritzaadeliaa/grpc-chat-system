"""
FastAPI Web Proxy Server
Bridge antara Web UI (HTTP/WebSocket) dan gRPC backend services.
Port: 8000

Fitur:
- WebSocket ↔ gRPC Bidirectional Streaming bridge
- Server-Initiated Events: metrics + alert setiap 5 detik
- Command & Control Bridge: /cmd via WebSocket → panggil gRPC RPC
- Rate Limiting: blokir spam pesan > 5 pesan/5 detik per user
- JWT Authentication: token digenerate saat login, divalidasi saat buka WS
"""

import asyncio
import json
import threading
import queue
import sys
import os
import random
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Set, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import grpc
from jose import jwt, JWTError

# Fix path untuk import pb2
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import user_pb2
import user_pb2_grpc
import room_pb2
import room_pb2_grpc
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

app = FastAPI(title="gRPC Chat System - Web Proxy")

# ─── JWT Config ───────────────────────────────────────────────────────────────
JWT_SECRET  = "grpc-chat-super-secret-key-2025"
JWT_ALGO    = "HS256"
JWT_EXPIRE  = 60  # menit

def create_token(username: str) -> str:
    """Generate JWT token saat user login berhasil."""
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE)
    return jwt.encode(
        {"sub": username, "exp": expire},
        JWT_SECRET, algorithm=JWT_ALGO
    )

def verify_token(token: str) -> Optional[dict]:
    """Verifikasi JWT. Return payload dict atau None jika invalid."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        return None


# ─── Rate Limiter ─────────────────────────────────────────────────────────────
class RateLimiter:
    """
    Sliding-window rate limiter per username.
    Default: maks 5 pesan dalam 5 detik.
    Jika dilanggar, server mengirim Server-Initiated Event peringatan.
    """
    def __init__(self, max_msgs: int = 5, window_sec: float = 5.0):
        self.max_msgs   = max_msgs
        self.window_sec = window_sec
        # { username: deque of timestamps }
        self._windows: Dict[str, deque] = {}

    def is_allowed(self, username: str) -> bool:
        now = time.monotonic()
        if username not in self._windows:
            self._windows[username] = deque()
        win = self._windows[username]
        # Buang timestamp yang sudah di luar window
        while win and now - win[0] > self.window_sec:
            win.popleft()
        if len(win) >= self.max_msgs:
            return False
        win.append(now)
        return True

rate_limiter = RateLimiter(max_msgs=5, window_sec=5.0)

# ─── User Store (in-memory auth) ──────────────────────────────────────────────
# Menyimpan { username: hashed_password } sebagai lapisan autentikasi
# di proxy level (UserService gRPC hanya mengelola sesi, bukan password).
import hashlib

_user_db: Dict[str, str] = {}   # { username: sha256(password) }

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def auth_user(username: str, password: str) -> str:
    """
    Registrasi otomatis jika user belum ada (first login = register).
    Return: 'ok' | 'wrong_password'
    """
    hashed = _hash_pw(password)
    if username not in _user_db:
        _user_db[username] = hashed   # auto-register
        return "ok"
    return "ok" if _user_db[username] == hashed else "wrong_password"

# ─── gRPC Channels & Stubs ────────────────────────────────────────────────────
user_channel  = grpc.insecure_channel('localhost:50052')
user_stub     = user_pb2_grpc.UserServiceStub(user_channel)

room_channel  = grpc.insecure_channel('localhost:50053')
room_stub     = room_pb2_grpc.RoomServiceStub(room_channel)

# ─── MQTT Client Setup ────────────────────────────────────────────────────────
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Dictionary to track subscribed rooms to avoid duplicate subscriptions
subscribed_rooms: Set[str] = set()
mqtt_loop: asyncio.AbstractEventLoop = None

retained_messages: Dict[str, dict] = {}
sys_metrics: Dict[str, str] = {}
dashboard_clients: Set[WebSocket] = set()

async def notify_dashboards(payload: dict):
    dead = []
    for ws in list(dashboard_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        dashboard_clients.discard(ws)

def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[WebProxy] Terhubung ke MQTT Broker!")
        # Subscribe ke topic LWT (Orang 3) dan SYS
        client.subscribe("alert/system")
        client.subscribe("$SYS/#")
        
        # Re-subscribe ke semua room aktif jika reconnect
        for room in subscribed_rooms:
            client.subscribe(f"chat/room/{room}")
    else:
        print(f"[WebProxy] Gagal connect MQTT, rc={rc}")

def on_mqtt_message(client, userdata, msg):
    """
    Callback saat pesan MQTT diterima.
    Berjalan di thread paho-mqtt, sehingga perlu dipush ke asyncio loop.
    """
    if mqtt_loop is None:
        return
        
    topic = msg.topic
    
    # ── Broker Metrics (SYS) ──
    if topic.startswith("$SYS/"):
        try:
            sys_metrics[topic] = msg.payload.decode()
        except:
            pass
        return
    
    # ── LWT Alert (Orang 3) ──
    if topic == "alert/system":
        try:
            payload = json.loads(msg.payload.decode())
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_to_all(payload),
                mqtt_loop
            )
        except Exception as e:
            print(f"[WebProxy] Gagal parse LWT message: {e}")
        return

    # ── Bot Response (Orang 3) ──
    if topic.startswith("chat/response/"):
        username = topic.split("/")[-1]
        try:
            payload = json.loads(msg.payload.decode())
            # Cari websocket user ini dan kirim
            # Kita broadcast ke semua room, tapi frontend/manager bisa difilter (untuk simplifikasi, kirim ke semua WS milik user)
            asyncio.run_coroutine_threadsafe(
                send_bot_response(username, payload),
                mqtt_loop
            )
        except Exception as e:
            print(f"[WebProxy] Gagal parse Bot Response: {e}")
        return

    # Cek apakah ini pesan chat room: chat/room/<room_name>
    if topic.startswith("chat/room/"):
        room = topic.split("/")[-1]
        
        # Ambil User Properties jika ada (MQTT v5)
        props = getattr(msg, "properties", None)
        user_props = {}
        if props and hasattr(props, "UserProperty"):
            user_props = dict(props.UserProperty)
            
        # Parse payload
        try:
            payload = json.loads(msg.payload.decode())
            # Jika user properties tersedia, kita override nilai di payload (membuktikan fitur jalan)
            if "username" in user_props:
                payload["username"] = user_props["username"]
            if "msg_type" in user_props:
                payload["type"] = user_props["msg_type"]
                
            # Cache retained message
            if payload.get("is_pin") or msg.retain:
                if payload.get("message") == "" and payload.get("type") != "join":
                    retained_messages.pop(room, None)
                else:
                    payload["is_pin"] = True
                    payload["_cached_at"] = time.time()
                    retained_messages[room] = payload
                
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_to_room(room, payload),
                mqtt_loop
            )
            
            # Broadcast log to dashboards
            dash_payload = dict(payload)
            dash_payload["_dash_type"] = "chat_log"
            asyncio.run_coroutine_threadsafe(
                notify_dashboards(dash_payload),
                mqtt_loop
            )
        except Exception as e:
            print(f"[WebProxy] Gagal parse MQTT message: {e}")

async def send_bot_response(username, payload):
    # Cari semua WS yang dimiliki oleh username ini dan kirim balasan
    for ws, info in manager.ws_info.items():
        if info["username"] == username:
            try:
                await ws.send_json(payload)
            except:
                pass

# Inisialisasi MQTT v5
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)

# Last Will Testament (LWT) - Orang 3
lwt_props = Properties(PacketTypes.WILLMESSAGE)
lwt_props.MessageExpiryInterval = 3600 # 1 Jam
mqtt_client.will_set("alert/system", json.dumps({
    "type": "server_alert",
    "level": "danger",
    "message": "🚨 Proxy Server Terputus! Coba muat ulang halaman.",
    "timestamp": "LWT"
}), qos=1, retain=True, properties=lwt_props)

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

# Dictionary untuk Topic Alias (menghemat bandwidth)
topic_aliases = {}
next_alias_id = 1


# ─── Connection Manager ───────────────────────────────────────────────────────
class ConnectionManager:
    """
    Mengelola semua koneksi WebSocket aktif.
    - connections: WebSocket per room { room: Set[WebSocket] }
    - ws_info    : metadata per WebSocket { ws: {username, room} }
    - all_ws     : seluruh WebSocket (untuk server-initiated broadcast)
    """

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.ws_info: Dict[WebSocket, dict] = {}
        self.all_ws: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket, username: str, room: str):
        await ws.accept()
        if room not in self.connections:
            self.connections[room] = set()
        self.connections[room].add(ws)
        self.ws_info[ws] = {"username": username, "room": room}
        self.all_ws.add(ws)

    def disconnect(self, ws: WebSocket):
        info = self.ws_info.pop(ws, None)
        if info:
            room = info["room"]
            self.connections.get(room, set()).discard(ws)
            if room in self.connections and not self.connections[room]:
                del self.connections[room]
        self.all_ws.discard(ws)

    async def broadcast_to_room(self, room: str, message: dict, exclude_ws: WebSocket = None):
        """Kirim pesan ke semua WebSocket di room tertentu."""
        targets = list(self.connections.get(room, set()))
        dead = []
        for ws in targets:
            if ws == exclude_ws:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_to_all(self, message: dict):
        """
        SERVER-INITIATED EVENT: Kirim pesan ke SEMUA WebSocket yang aktif.
        Dipanggil oleh background task untuk push metrics / alert.
        """
        dead = []
        for ws in list(self.all_ws):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to_ws(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            self.disconnect(ws)

    def get_room_usernames(self, room: str) -> list:
        """Kembalikan daftar username yang sedang online di room tertentu."""
        return [
            self.ws_info[ws]["username"]
            for ws in self.connections.get(room, set())
            if ws in self.ws_info
        ]

    @property
    def total_connections(self) -> int:
        return len(self.all_ws)


manager = ConnectionManager()
qos_stats = {0: 0, 1: 0, 2: 0}


# ─── Server-Initiated Events: Background Metrics Broadcaster ──────────────────
# Cooldown untuk CPU alert agar tidak spam (tidak relevan lagi tapi dibiarkan strukturnya)
_last_cpu_alert = 0
_CPU_ALERT_COOLDOWN = 300  # 5 menit (agar tidak mengganggu chat)

def _get_mqtt_metrics() -> dict:
    """Mengambil data statistik QoS asli dan metrik sistem Broker."""
    # Garbage collect expired retained messages
    now = time.time()
    for r in list(retained_messages.keys()):
        rm = retained_messages[r]
        exp = int(rm.get("expiry", 0))
        if exp > 0 and (now - rm.get("_cached_at", 0)) >= exp:
            del retained_messages[r]
            
    return {
        "qos0": qos_stats[0],
        "qos1": qos_stats[1],
        "qos2": qos_stats[2],
        "connections": manager.total_connections,
        "uptime_s": int(time.monotonic()),
        "sys": sys_metrics,
        "active_rooms": list(subscribed_rooms),
        "retained_count": len(retained_messages)
    }


# Daftar pesan maintenance acak untuk Server-Initiated Events
_MAINTENANCE_ALERTS = [
    ("warning", "🔧 Maintenance dijadwalkan dalam 10 menit. Harap selesaikan percakapan penting."),
    ("info",    "📡 Sistem berjalan normal. Ping dari server berhasil."),
    ("info",    "🔄 Auto-backup database chat sedang berjalan di latar belakang."),
    ("warning", "⚡ Beban jaringan meningkat. Latency mungkin sedikit bertambah."),
    ("info",    "✅ Health check: Semua layanan gRPC aktif dan responsif."),
]
_alert_idx = 0


async def server_metrics_broadcaster():
    """
    SERVER-INITIATED EVENTS — Background task yang berjalan selamanya.
    Setiap 2 detik mem-push data metrics ke semua browser tanpa diminta klien.
    """
    global _alert_idx, _last_cpu_alert
    tick = 0
    while True:
        await asyncio.sleep(2)
        if manager.total_connections == 0:
            continue

        metrics = _get_mqtt_metrics()
        tick += 2


        # Kirim paket server_metric ke semua klien setiap 2 detik
        await manager.broadcast_to_all({
            "type":      "server_metric",
            "data":      metrics,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })

        # ── Server-Initiated Alert: (Diabaikan untuk metrics dashboard asli) ──
        now = time.monotonic()

        # ── Server-Initiated Alert: periodic system notices (~60 detik sekali) ──
        if tick % 60 == 0:
            level, msg = _MAINTENANCE_ALERTS[_alert_idx % len(_MAINTENANCE_ALERTS)]
            _alert_idx += 1
            await manager.broadcast_to_all({
                "type":    "server_alert",
                "level":   level,
                "message": msg,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })


@app.on_event("startup")
async def startup_event():
    """Jalankan background task saat server startup."""
    global mqtt_loop
    mqtt_loop = asyncio.get_event_loop()
    
    # Konek ke MQTT Broker (asinkron di background thread)
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"[WebProxy] PERINGATAN: Gagal connect ke MQTT Broker: {e}")

    asyncio.create_task(server_metrics_broadcaster())
    print("[WebProxy] Server-Initiated Events broadcaster started.")


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/login")
async def login(body: dict):
    """
    Step 1 Login: Terima username + password, validasi, lalu kembalikan JWT.
    - Jika user belum pernah ada → auto-register (first login = daftar).
    - Jika user sudah ada → verifikasi password.
    - Jika sukses → panggil gRPC UserService.Login dan kembalikan JWT token.
    """
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username tidak boleh kosong")
    if not password:
        raise HTTPException(status_code=400, detail="Password tidak boleh kosong")

    # Validasi password (in-memory, auto-register jika belum ada)
    is_new = username not in _user_db
    result = auth_user(username, password)
    if result == "wrong_password":
        raise HTTPException(status_code=401, detail="Password salah! Silakan coba lagi.")

    # Panggil gRPC UserService
    try:
        resp = user_stub.Login(user_pb2.UserRequest(username=username))
        token = create_token(username)
        msg = f"Selamat datang kembali, {username}!" if not is_new else f"Akun '{username}' berhasil dibuat!"
        return {"status": "SUCCESS", "message": msg, "token": token, "is_new": is_new}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


@app.post("/api/reset-password")
async def reset_password(body: dict):
    """(Simulasi) Mereset password untuk user yang lupa"""
    username = body.get("username", "").strip()
    new_password = body.get("new_password", "").strip()
    
    if not username or not new_password:
        raise HTTPException(status_code=400, detail="Username dan password baru wajib diisi!")
    if username not in _user_db:
        raise HTTPException(status_code=404, detail="Username tidak ditemukan di sistem!")
        
    # Langsung timpa password lamanya dengan hash baru
    _user_db[username] = _hash_pw(new_password)
    return {"status": "SUCCESS", "message": f"Password untuk {username} berhasil di-reset!"}



@app.post("/api/logout")
async def logout(body: dict):
    """Logout dari UserService via gRPC."""
    username = body.get("username", "").strip()
    try:
        resp = user_stub.Logout(user_pb2.UserRequest(username=username))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


@app.post("/api/join-room")
async def join_room(body: dict):
    """Bergabung ke room via gRPC."""
    username = body.get("username", "").strip()
    room     = body.get("room", "").strip()
    if not username or not room:
        raise HTTPException(status_code=400, detail="Username dan room tidak boleh kosong")
    try:
        resp = room_stub.JoinRoom(room_pb2.RoomRequest(username=username, room=room))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


@app.post("/api/leave-room")
async def leave_room(body: dict):
    """Keluar dari room via gRPC."""
    username = body.get("username", "").strip()
    room     = body.get("room", "").strip()
    try:
        resp = room_stub.LeaveRoom(room_pb2.RoomRequest(username=username, room=room))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


# ─── Command & Control Handler ────────────────────────────────────────────────

async def handle_command(ws: WebSocket, username: str, room: str, command: str, args: str):
    """
    COMMAND & CONTROL BRIDGE.
    Menerima instruksi dari browser via WebSocket, memanggil fungsi gRPC
    yang sesuai di layanan back-end, lalu mengembalikan hasilnya ke klien.

    Commands yang didukung:
      get_members         → RoomService.GetRoomMembers
      ping_services       → Cek konektivitas semua gRPC services
      broadcast <pesan>   → Kirim system-announcement ke seluruh room
    """
    ts = datetime.now().strftime("%H:%M:%S")

    try:
        if command == "get_members":
            # ── Panggil gRPC RoomService.GetRoomMembers ──────────────────────────
            try:
                resp = room_stub.GetRoomMembers(
                    room_pb2.RoomRequest(username=username, room=room)
                )
                members = resp.message.split(",") if resp.message else []
                members_clean = [m.strip() for m in members if m.strip()]
                result_text = (
                    f"👥 Anggota room '{room}': {', '.join(members_clean)}"
                    if members_clean
                    else f"Room '{room}' saat ini kosong."
                )
                await manager.send_to_ws(ws, {
                    "type":    "command_result",
                    "command": command,
                    "success": True,
                    "result":  result_text,
                    "timestamp": ts,
                })
            except grpc.RpcError as e:
                await manager.send_to_ws(ws, {
                    "type":    "command_result",
                    "command": command,
                    "success": False,
                    "result":  f"gRPC error: {e.details()}",
                    "timestamp": ts,
                })

        elif command == "ping_services":
            # ── Cek health ke semua gRPC services ────────────────────────────────
            services = [
                ("UserService  (port 50052)", user_stub.Login,          user_pb2.UserRequest(username="_ping_")),
                ("RoomService  (port 50053)", room_stub.GetRoomMembers, room_pb2.RoomRequest(username="_ping_", room="_ping_")),
                ("ChatService  (MQTT Broker)", None,                     None),
            ]
            results = []
            for svc_name, method, req in services:
                if method is None:
                    # Cek koneksi broker
                    try:
                        if mqtt_client.is_connected():
                            results.append(f"✅ {svc_name}: ONLINE")
                        else:
                            results.append(f"❌ {svc_name}: OFFLINE")
                    except Exception:
                        results.append(f"❌ {svc_name}: OFFLINE atau tidak merespons")
                else:
                    try:
                        method(req, timeout=2)
                        results.append(f"✅ {svc_name}: ONLINE")
                    except grpc.RpcError:
                        # RpcError berarti server bisa dijangkau (hanya request-nya ditolak)
                        results.append(f"✅ {svc_name}: ONLINE (reachable)")
                    except Exception as ex:
                        results.append(f"❌ {svc_name}: OFFLINE ({ex})")

            await manager.send_to_ws(ws, {
                "type":    "command_result",
                "command": command,
                "success": True,
                "result":  "🔍 PING RESULTS:\n" + "\n".join(results),
                "timestamp": ts,
            })

        elif command == "broadcast":
            # ── Kirim system-announcement ke seluruh anggota room ────────────────
            announcement = args.strip() if args else "(pesan kosong)"
            await manager.broadcast_to_room(room, {
                "type":      "server_alert",
                "level":     "info",
                "message":   f"📢 Pengumuman dari {username}: {announcement}",
                "timestamp": ts,
            })
            await manager.send_to_ws(ws, {
                "type":    "command_result",
                "command": command,
                "success": True,
                "result":  f"Pengumuman terkirim ke room '{room}'.",
                "timestamp": ts,
            })

        else:
            await manager.send_to_ws(ws, {
                "type":    "command_result",
                "command": command,
                "success": False,
                "result":  (
                    f"❓ Command tidak dikenal: '{command}'\n"
                    "Perintah tersedia:\n"
                    "  /cmd get_members\n"
                    "  /cmd ping_services\n"
                    "  /cmd broadcast <pesan>"
                ),
                "timestamp": ts,
            })

    except Exception as e:
        # Tangkap semua exception agar tidak crash WebSocket
        print(f"[WebProxy] handle_command error ({command}): {e}")
        try:
            await manager.send_to_ws(ws, {
                "type":    "command_result",
                "command": command,
                "success": False,
                "result":  f"❌ Internal error saat memproses command: {e}",
                "timestamp": ts,
            })
        except Exception:
            pass


# ─── WebSocket Chat Endpoint ───────────────────────────────────────────────────

@app.websocket("/ws/chat/{username}/{room}")
async def websocket_chat(
    ws: WebSocket,
    username: str,
    room: str,
    token: str = Query(default=""),
):
    """
    WebSocket endpoint untuk real-time chat.

    AUTENTIKASI JWT:
      Browser menyertakan token (diperoleh dari /api/login) sebagai
      query parameter: /ws/chat/{username}/{room}?token=<JWT>
      Server memvalidasi token sebelum menerima koneksi. Jika invalid,
      koneksi langsung ditutup dengan kode 4001.

    Flow:
    1. Validasi JWT token
    2. Proxy membuka gRPC bidirectional stream ke ChatService
    3. Pesan dari WebSocket → Rate Limiter → gRPC stream (atau command)
    4. Pesan dari gRPC stream → di-forward ke WebSocket ini
    5. Background task mem-push metrics/alert ke WS ini via broadcast_to_all
    """
    # ── Validasi JWT ────────────────────────────────────────────────────
    payload = verify_token(token) if token else None
    if payload is None:
        await ws.accept()
        await ws.send_json({
            "type":    "server_alert",
            "level":   "danger",
            "message": "🔐 Autentikasi gagal: Token JWT tidak valid atau sudah expired. Silakan login ulang.",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        await ws.close(code=4001)
        print(f"[WebProxy] JWT rejected for {username}")
        return

    # Pastikan token memang milik user ini
    if payload.get("sub") != username:
        await ws.accept()
        await ws.send_json({
            "type":    "server_alert",
            "level":   "danger",
            "message": "🚫 Token tidak sesuai dengan username. Akses ditolak.",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        await ws.close(code=4001)
        return

    print(f"[WebProxy] JWT OK ✓ {username} @ {room}")
    await manager.connect(ws, username, room)
    print(f"[WebProxy] WebSocket connected: {username} @ {room}")

    # Kirim retained message ke user baru jika ada
    if room in retained_messages:
        rm = retained_messages[room]
        exp = int(rm.get("expiry", 0))
        if exp > 0 and (time.time() - rm.get("_cached_at", 0)) >= exp:
            del retained_messages[room]
        else:
            await manager.send_to_ws(ws, rm)

    # ── Subscribe MQTT ke Room (Jika Belum) ──────────────────────────────
    if room not in subscribed_rooms:
        subscribed_rooms.add(room)
        mqtt_client.subscribe(f"chat/room/{room}")
        print(f"[WebProxy] Subscribed ke MQTT topic: chat/room/{room}")

    # Kirim sinyal join ke MQTT (menggunakan User Properties MQTT v5)
    join_props = Properties(PacketTypes.PUBLISH)
    join_props.UserProperty = [("username", username), ("msg_type", "join")]
    
    join_payload = json.dumps({
        "message": "", 
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        # username & msg_type sengaja dihapus dari payload untuk mendemokan User Properties
    })
    mqtt_client.publish(f"chat/room/{room}", join_payload, properties=join_props)

    # Subscribe ke topic response bot (Orang 3)
    response_topic = f"chat/response/{username}"
    mqtt_client.subscribe(response_topic)

    # Notifikasi join ke room — termasuk daftar user online terkini
    await manager.broadcast_to_room(room, {
        "type":         "system",
        "message":      f"✅ {username} bergabung ke room '{room}'",
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
        "online_users": manager.get_room_usernames(room),
    })

    try:
        while True:
            data = await ws.receive_text()
            msg_dict = json.loads(data)
            msg_type = msg_dict.get("type", "message")

            # ── COMMAND & CONTROL BRIDGE ──────────────────────────────────────
            if msg_type == "command":
                command = msg_dict.get("command", "").strip()
                args    = msg_dict.get("args", "").strip()
                # Handle command secara async di event loop (tidak perlu thread)
                asyncio.ensure_future(
                    handle_command(ws, username, room, command, args)
                )
                continue

            # ── CHAT / TYPING MESSAGE → gRPC Stream ──────────────────────────
            text      = msg_dict.get("message", "").strip()
            timestamp = datetime.now().strftime("%H:%M:%S")

            if msg_type == "message" and not text:
                continue

            # ── Rate Limiter: hanya pesan "message" yang dihitung ──
            if msg_type == "message":
                if not rate_limiter.is_allowed(username):
                    # Server-Initiated Event: dorong peringatan spam
                    await manager.send_to_ws(ws, {
                        "type":    "server_alert",
                        "level":   "warning",
                        "message": f"⚠️ Rate limit: Kamu mengirim pesan terlalu cepat, {username}! Tunggu beberapa detik.",
                        "timestamp": timestamp,
                    })
                    print(f"[RateLimit] ⚠ {username} blocked (spam)")
                    continue

            # ── Publish pesan via MQTT (dengan Topic Alias & User Properties) ──
            global next_alias_id
            
            # Ambil opsi MQTT dari frontend (QoS, Retain, Expiry, Bot Command)
            qos = int(msg_dict.get("qos", 0))
            retain = bool(msg_dict.get("retain", False))
            expiry = msg_dict.get("expiry", 0) # dalam detik, 0 = no expiry
            
            # --- Rekam metrik QoS (jika ini pesan chat biasa, bukan typing dll) ---
            if msg_type == "message" and not text.startswith("/bot "):
                if qos in qos_stats:
                    qos_stats[qos] += 1
            # ----------------------------------------------------------------------
            
            # ── Request-Response Bot (Orang 3) ──
            if text.startswith("/bot "):
                command = text[5:].strip()
                bot_req_topic = "chat/request/bot"
                bot_res_topic = f"chat/response/{username}"
                
                req_props = Properties(PacketTypes.PUBLISH)
                req_props.ResponseTopic = bot_res_topic
                req_props.UserProperty = [("user_id", username)]
                
                payload = json.dumps({"command": command, "user_id": username})
                mqtt_client.publish(bot_req_topic, payload, qos=1, properties=req_props)
                
                # Kasih feedback sementara ke user di room
                await manager.send_to_ws(ws, {
                    "type": "system",
                    "message": f"⏳ Sedang meminta bot untuk perintah: '{command}'...",
                    "timestamp": timestamp
                })
                continue

            topic = f"chat/room/{room}"
            
            publish_props = Properties(PacketTypes.PUBLISH)
            publish_props.UserProperty = [("username", username), ("msg_type", msg_type)]
            
            # Fitur Message Expiry (Orang 3)
            if expiry > 0:
                publish_props.MessageExpiryInterval = int(expiry)
            
            # Gunakan Topic Alias jika tersedia
            if topic in topic_aliases:
                publish_props.TopicAlias = topic_aliases[topic]
                publish_topic = "" # Kosongkan string topik karena alias digunakan
            else:
                topic_aliases[topic] = next_alias_id
                publish_props.TopicAlias = next_alias_id
                publish_topic = topic
                next_alias_id += 1

            payload = json.dumps({
                "message": text,
                "timestamp": timestamp,
                "type": msg_type,
                "username": username,
                "room": room,
                "is_pin": retain, # Tandai sebagai pesan pinned
                "expiry": expiry
            })
            
            mqtt_client.publish(publish_topic, payload, qos=qos, retain=retain, properties=publish_props)

    except WebSocketDisconnect:
        print(f"[WebProxy] WebSocket disconnected: {username} @ {room}")
    except Exception as e:
        print(f"[WebProxy] WebSocket error: {e}")
    finally:
        # Cleanup WebSocket (tidak ada lagi queue untuk grpc thread)
        manager.disconnect(ws)

        await manager.broadcast_to_room(room, {
            "type":         "system",
            "message":      f"❌ {username} meninggalkan room '{room}'",
            "timestamp":    datetime.now().strftime("%H:%M:%S"),
            "online_users": manager.get_room_usernames(room),
        })

        try:
            room_stub.LeaveRoom(room_pb2.RoomRequest(username=username, room=room))
            user_stub.Logout(user_pb2.UserRequest(username=username))
        except Exception:
            pass


# ─── Serve Static Files ────────────────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve Web UI."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Web UI not found</h1>")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve Dashboard Web UI."""
    html_path = os.path.join(os.path.dirname(__file__), "web", "dashboard.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Dashboard not found</h1>")

@app.websocket("/ws/dashboard")
async def websocket_dashboard(ws: WebSocket):
    """Endpoint untuk dashboard menerima broadcast metrik tanpa auth."""
    await ws.accept()
    manager.all_ws.add(ws)
    dashboard_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        manager.all_ws.discard(ws)
        dashboard_clients.discard(ws)

@app.get("/health")
async def health():
    return {"status": "ok", "services": {
        "user":  "localhost:50052",
        "room":  "localhost:50053",
        "chat":  "MQTT Broker @ localhost:1883",
        "proxy": "localhost:8000",
    }, "active_connections": manager.total_connections}


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("🚀  gRPC Chat Web Proxy  →  http://localhost:8000")
    print("    Server-Initiated Events: aktif (interval 3 detik)")
    print("    Command & Control Bridge: aktif")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
