import grpc
from concurrent import futures
import time
import queue
import threading
import sys
import os

# Fix import path - add root project directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import chat_pb2
import chat_pb2_grpc

# In-memory connection tracking:
# { room_name: { username: Queue } }
clients = {}
lock = threading.Lock()


class ChatService(chat_pb2_grpc.ChatServiceServicer):

    def ChatStream(self, request_iterator, context):
        """
        Bidirectional Streaming RPC.
        - Setiap client yang connect akan punya Queue sendiri.
        - Thread receiver akan membaca pesan masuk dan broadcast ke semua client di room.
        - Main thread (generator) akan mengirim pesan dari queue ke client.
        """
        print("[ChatService] Client terhubung")

        q = queue.Queue()
        username = None
        user_room = None

        def receive_messages():
            """Thread untuk menerima pesan dari client dan broadcast ke room."""
            nonlocal username, user_room

            try:
                for message in request_iterator:
                    username = message.username
                    user_room = message.room

                    # Daftarkan client ke room saat pertama kali kirim pesan
                    with lock:
                        if user_room not in clients:
                            clients[user_room] = {}

                        if username not in clients[user_room]:
                            clients[user_room][username] = q
                            print(f"[ChatService] {username} terdaftar di room '{user_room}'")

                    # Log pesan masuk
                    print(f"[ChatService] [{user_room}] {username}: {message.message}")

                    # Broadcast ke semua user di room yang sama
                    with lock:
                        for user, client_queue in list(clients.get(user_room, {}).items()):
                            # Kirim ke semua termasuk pengirim sendiri agar muncul di UI
                            client_queue.put(message)

            except Exception as e:
                print(f"[ChatService] receive_messages error: {e}")

            finally:
                # Cleanup saat client disconnect
                with lock:
                    if user_room and username:
                        if user_room in clients and username in clients[user_room]:
                            del clients[user_room][username]
                            print(f"[ChatService] {username} disconnected dari '{user_room}'")

                        # Hapus room kalau sudah kosong
                        if user_room in clients and not clients[user_room]:
                            del clients[user_room]
                            print(f"[ChatService] Room '{user_room}' dihapus (kosong)")

                # Kirim sentinel ke queue agar main thread berhenti
                q.put(None)

        # Jalankan receiver di thread terpisah
        t = threading.Thread(target=receive_messages, daemon=True)
        t.start()

        # Main thread: kirim pesan dari queue ke client (yield)
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
            # Pastikan cleanup juga terjadi jika terjadi error dari sisi yield
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