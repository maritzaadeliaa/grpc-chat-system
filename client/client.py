"""
gRPC Chat System - CLI Client (Fixed)
Mendukung send & receive secara bersamaan menggunakan threading.

Usage: python -m client.client
"""

import grpc
import threading
import sys
import os
from datetime import datetime

# Fix import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import user_pb2
import user_pb2_grpc
import room_pb2
import room_pb2_grpc
import chat_pb2
import chat_pb2_grpc

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
GRAY   = "\033[90m"


def run():
    print(f"\n{BOLD}{'=' * 45}{RESET}")
    print(f"{BOLD}  💬 gRPC Chat System - CLI Client{RESET}")
    print(f"{BOLD}{'=' * 45}{RESET}\n")

    username = input(f"{BOLD}Username : {RESET}").strip()
    room     = input(f"{BOLD}Room     : {RESET}").strip()

    if not username or not room:
        print(f"{RED}❌ Username dan room tidak boleh kosong!{RESET}")
        return

    # ── 1. Login via UserService ──────────────────────────
    try:
        user_channel = grpc.insecure_channel('localhost:50052')
        user_stub = user_pb2_grpc.UserServiceStub(user_channel)
        login_res = user_stub.Login(user_pb2.UserRequest(username=username))

        if login_res.status != "SUCCESS":
            print(f"{RED}❌ {login_res.message}{RESET}")
            return
        print(f"{GREEN}✅ {login_res.message}{RESET}")
    except grpc.RpcError as e:
        print(f"{RED}❌ User Service tidak bisa dihubungi: {e.details()}{RESET}")
        print(f"{YELLOW}   Pastikan user_server.py sudah berjalan di port 50052{RESET}")
        return

    # ── 2. Join Room via RoomService ──────────────────────
    try:
        room_channel = grpc.insecure_channel('localhost:50053')
        room_stub = room_pb2_grpc.RoomServiceStub(room_channel)
        room_res = room_stub.JoinRoom(room_pb2.RoomRequest(username=username, room=room))
        print(f"{GREEN}✅ {room_res.message}{RESET}")
    except grpc.RpcError as e:
        print(f"{RED}❌ Room Service tidak bisa dihubungi: {e.details()}{RESET}")
        print(f"{YELLOW}   Pastikan room_server.py sudah berjalan di port 50053{RESET}")
        return

    # ── 3. Connect ke ChatService via Bidirectional Stream ─
    try:
        chat_channel = grpc.insecure_channel('localhost:50051')
        chat_stub = chat_pb2_grpc.ChatServiceStub(chat_channel)
    except Exception as e:
        print(f"{RED}❌ Tidak bisa konek ke Chat Service: {e}{RESET}")
        return

    print(f"\n{BOLD}{'─' * 45}{RESET}")
    print(f"  Room  : {CYAN}{room}{RESET}")
    print(f"  User  : {CYAN}{username}{RESET}")
    print(f"{BOLD}{'─' * 45}{RESET}")
    print(f"  {GRAY}Ketik pesan lalu tekan Enter untuk kirim.{RESET}")
    print(f"  {GRAY}Ketik /keluar untuk keluar.{RESET}")
    print(f"{BOLD}{'─' * 45}{RESET}\n")

    import queue
    send_q = queue.Queue()
    stop_event = threading.Event()

    def message_generator():
        while not stop_event.is_set():
            try:
                msg = send_q.get(timeout=0.5)
                if msg is None:
                    return
                yield msg
            except queue.Empty:
                continue

    def receive_thread():
        """Thread untuk menerima pesan dari server."""
        try:
            responses = chat_stub.ChatStream(message_generator())
            for resp in responses:
                if stop_event.is_set():
                    break
                ts = resp.timestamp or datetime.now().strftime("%H:%M:%S")
                if resp.username == username:
                    print(f"\r{GRAY}[{ts}]{RESET} {BOLD}{GREEN}Kamu{RESET}: {resp.message}")
                else:
                    print(f"\r{GRAY}[{ts}]{RESET} {BOLD}{CYAN}{resp.username}{RESET}: {resp.message}")
                print(f"{BOLD}>> {RESET}", end='', flush=True)
        except grpc.RpcError as e:
            if not stop_event.is_set():
                print(f"\n{RED}❌ Koneksi terputus: {e.details()}{RESET}")
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n{RED}❌ Error: {e}{RESET}")
        finally:
            stop_event.set()

    # Jalankan receiver di background
    t = threading.Thread(target=receive_thread, daemon=True)
    t.start()

    # Main thread: baca input dari user
    try:
        while not stop_event.is_set():
            print(f"{BOLD}>> {RESET}", end='', flush=True)
            text = sys.stdin.readline()
            if not text:
                break

            text = text.strip()
            if text == '/keluar':
                break
            if not text:
                continue

            ts = datetime.now().strftime("%H:%M:%S")
            send_q.put(chat_pb2.ChatMessage(
                username=username,
                room=room,
                message=text,
                timestamp=ts
            ))
    except KeyboardInterrupt:
        pass

    # Cleanup
    stop_event.set()
    send_q.put(None)

    try:
        room_stub.LeaveRoom(room_pb2.RoomRequest(username=username, room=room))
        user_stub.Logout(user_pb2.UserRequest(username=username))
    except Exception:
        pass

    print(f"\n{YELLOW}👋 Kamu telah keluar dari {room}. Sampai jumpa, {username}!{RESET}\n")


if __name__ == '__main__':
    run()