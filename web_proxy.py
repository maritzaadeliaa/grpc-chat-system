"""
FastAPI Web Proxy Server
Bridge antara Web UI (HTTP/WebSocket) dan gRPC backend services.
Port: 8000
"""

import asyncio
import json
import threading
import queue
import sys
import os
from datetime import datetime
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import grpc

# Fix path untuk import pb2
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import user_pb2
import user_pb2_grpc
import room_pb2
import room_pb2_grpc
import chat_pb2
import chat_pb2_grpc

app = FastAPI(title="gRPC Chat System - Web Proxy")

# ─── gRPC Channels & Stubs ────────────────────────────────────────────────────
user_channel = grpc.insecure_channel('localhost:50052')
user_stub = user_pb2_grpc.UserServiceStub(user_channel)

room_channel = grpc.insecure_channel('localhost:50053')
room_stub = room_pb2_grpc.RoomServiceStub(room_channel)

chat_channel = grpc.insecure_channel('localhost:50051')
chat_stub = chat_pb2_grpc.ChatServiceStub(chat_channel)

# ─── WebSocket Connection Manager ─────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # { room: Set[WebSocket] }
        self.connections: Dict[str, Set[WebSocket]] = {}
        # { websocket: { username, room } }
        self.ws_info: Dict[WebSocket, dict] = {}

    async def connect(self, ws: WebSocket, username: str, room: str):
        await ws.accept()
        if room not in self.connections:
            self.connections[room] = set()
        self.connections[room].add(ws)
        self.ws_info[ws] = {"username": username, "room": room}

    def disconnect(self, ws: WebSocket):
        info = self.ws_info.pop(ws, None)
        if info:
            room = info["room"]
            self.connections.get(room, set()).discard(ws)
            if room in self.connections and not self.connections[room]:
                del self.connections[room]

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

    async def send_to_ws(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            self.disconnect(ws)


manager = ConnectionManager()


# ─── REST Endpoints ───────────────────────────────────────────────────────────

@app.post("/api/login")
async def login(body: dict):
    """Login ke UserService via gRPC."""
    username = body.get("username", "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username tidak boleh kosong")

    try:
        resp = user_stub.Login(user_pb2.UserRequest(username=username))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


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
    room = body.get("room", "").strip()
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
    room = body.get("room", "").strip()
    try:
        resp = room_stub.LeaveRoom(room_pb2.RoomRequest(username=username, room=room))
        return {"status": resp.status, "message": resp.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e.details()))


# ─── WebSocket Chat Endpoint ───────────────────────────────────────────────────

@app.websocket("/ws/chat/{username}/{room}")
async def websocket_chat(ws: WebSocket, username: str, room: str):
    """
    WebSocket endpoint untuk real-time chat.
    Flow:
    1. Client connect ke WebSocket
    2. Proxy membuka stream gRPC ke ChatService
    3. Pesan dari WebSocket → dikirim ke gRPC stream
    4. Pesan dari gRPC stream → di-broadcast ke semua WebSocket di room
    """
    await manager.connect(ws, username, room)
    print(f"[WebProxy] WebSocket connected: {username} @ {room}")

    # Queue untuk mengirim pesan dari WebSocket ke gRPC generator
    send_queue = queue.Queue()
    # Event untuk menghentikan loop
    stop_event = threading.Event()

    def grpc_message_generator():
        """Generator yang menghasilkan pesan dari queue untuk dikirim ke gRPC."""
        while not stop_event.is_set():
            try:
                msg = send_queue.get(timeout=1.0)
                if msg is None:
                    return
                yield msg
            except queue.Empty:
                continue

    # ── jalankan gRPC stream di thread terpisah ──
    loop = asyncio.get_event_loop()
    grpc_error = [None]

    def run_grpc_stream():
        """Thread yang menjalankan gRPC streaming dan memforward pesan ke WebSocket.

        PENTING: Kirim hanya ke WebSocket milik stream INI (send_to_ws), bukan ke
        semua user (broadcast_to_room). Broadcasting sudah diurus oleh Chat Server
        di level gRPC queue — setiap user punya queue sendiri dan sudah menerima
        pesan dari sana. Kalau kita broadcast lagi di sini, setiap pesan akan
        muncul 2x (double bubble).
        """
        try:
            for response in chat_stub.ChatStream(grpc_message_generator()):
                msg_data = {
                    "type": "message",
                    "username": response.username,
                    "room": response.room,
                    "message": response.message,
                    "timestamp": response.timestamp or datetime.now().strftime("%H:%M:%S")
                }
                # Kirim HANYA ke WebSocket pemilik stream ini
                asyncio.run_coroutine_threadsafe(
                    manager.send_to_ws(ws, msg_data),
                    loop
                )
        except grpc.RpcError as e:
            grpc_error[0] = str(e)
        except Exception as e:
            grpc_error[0] = str(e)
        finally:
            stop_event.set()

    grpc_thread = threading.Thread(target=run_grpc_stream, daemon=True)
    grpc_thread.start()

    # ── kirim notifikasi join ke room ──
    join_msg = {
        "type": "system",
        "message": f"✅ {username} bergabung ke room '{room}'",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    await manager.broadcast_to_room(room, join_msg)

    # ── loop menerima pesan dari WebSocket ──
    try:
        while True:
            data = await ws.receive_text()
            msg_dict = json.loads(data)
            text = msg_dict.get("message", "").strip()

            if not text:
                continue

            timestamp = datetime.now().strftime("%H:%M:%S")

            # Masukkan ke queue untuk dikirim ke gRPC
            send_queue.put(chat_pb2.ChatMessage(
                username=username,
                room=room,
                message=text,
                timestamp=timestamp
            ))

    except WebSocketDisconnect:
        print(f"[WebProxy] WebSocket disconnected: {username} @ {room}")
    except Exception as e:
        print(f"[WebProxy] WebSocket error: {e}")
    finally:
        # Cleanup
        stop_event.set()
        send_queue.put(None)  # Unblock generator
        manager.disconnect(ws)

        # Notifikasi leave ke room
        leave_msg = {
            "type": "system",
            "message": f"❌ {username} meninggalkan room '{room}'",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        await manager.broadcast_to_room(room, leave_msg)

        # Leave room di gRPC
        try:
            room_stub.LeaveRoom(room_pb2.RoomRequest(username=username, room=room))
            user_stub.Logout(user_pb2.UserRequest(username=username))
        except Exception:
            pass


# ─── Serve Static Files ────────────────────────────────────────────────────────

# Mount static folder jika ada
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


@app.get("/health")
async def health():
    return {"status": "ok", "services": {
        "user": "localhost:50052",
        "room": "localhost:50053",
        "chat": "localhost:50051",
        "proxy": "localhost:8000"
    }}


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🚀 gRPC Chat Web Proxy starting on http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
