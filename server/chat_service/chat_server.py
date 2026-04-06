import grpc
from concurrent import futures
import time
import queue
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import chat_pb2
import chat_pb2_grpc

# { room_name: { username: Queue } }
clients = {}
lock = threading.Lock()


class ChatService(chat_pb2_grpc.ChatServiceServicer):

    def ChatStream(self, request_iterator, context):
        q = queue.Queue()
        username = None
        user_room = None

        def receive_messages():
            nonlocal username, user_room

            try:
                for message in request_iterator:
                    if not message.username or not message.room:
                        continue

                    username = message.username
                    user_room = message.room

                    # ── Registrasi ke room (selalu, termasuk saat join) ──
                    with lock:
                        if user_room not in clients:
                            clients[user_room] = {}
                        if username not in clients[user_room]:
                            clients[user_room][username] = q
                            print(f"[ChatService] {username} terdaftar di room '{user_room}'")

                    # ── Join signal: hanya register, tidak di-broadcast ──
                    if message.msg_type == "join":
                        continue

                    # ── Typing: broadcast tapi log ringkas ──
                    if message.msg_type == "typing":
                        with lock:
                            for user, cq in list(clients.get(user_room, {}).items()):
                                if user != username:   # jangan kirim balik ke pengirim
                                    cq.put(message)
                        continue

                    # ── Pesan biasa: log + broadcast ke semua termasuk pengirim ──
                    print(f"[ChatService] [{user_room}] {username}: {message.message}")
                    with lock:
                        for user, cq in list(clients.get(user_room, {}).items()):
                            cq.put(message)

            except Exception as e:
                print(f"[ChatService] receive error: {e}")
            finally:
                with lock:
                    if user_room and username:
                        if user_room in clients and username in clients[user_room]:
                            del clients[user_room][username]
                            print(f"[ChatService] {username} keluar dari '{user_room}'")
                        if user_room in clients and not clients[user_room]:
                            del clients[user_room]
                q.put(None)

        t = threading.Thread(target=receive_messages, daemon=True)
        t.start()

        try:
            while context.is_active():
                try:
                    message = q.get(timeout=1.0)
                    if message is None:
                        break
                    yield message
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"[ChatService] stream error: {e}")
        finally:
            with lock:
                if user_room and username:
                    if user_room in clients and username in clients[user_room]:
                        del clients[user_room][username]
                    if user_room in clients and not clients[user_room]:
                        del clients[user_room]
            print(f"[ChatService] Stream selesai untuk {username}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("=" * 40)
    print("[OK] Chat Server running on port 50051")
    print("=" * 40)
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        print("\n[ChatService] Server stopped.")


if __name__ == '__main__':
    serve()