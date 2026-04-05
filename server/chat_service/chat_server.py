import grpc
from concurrent import futures
import time
import queue
import threading

import chat_pb2
import chat_pb2_grpc

# room -> { username: queue }
clients = {}
lock = threading.Lock()


class ChatService(chat_pb2_grpc.ChatServiceServicer):

    def ChatStream(self, request_iterator, context):
        print("Client connected")

        q = queue.Queue()
        username = None
        user_room = None

        try:
            def receive_messages():
                nonlocal username, user_room

                for message in request_iterator:
                    username = message.username
                    user_room = message.room

                    # join room otomatis
                    with lock:
                        if user_room not in clients:
                            clients[user_room] = {}

                        if username not in clients[user_room]:
                            clients[user_room][username] = q
                            print(f"{username} joined {user_room}")

                    # broadcast ke room yg sama
                    with lock:
                        for user, client_queue in clients[user_room].items():
                            # skip sender biar gak double
                            if user != username:
                                client_queue.put(message)

            threading.Thread(target=receive_messages, daemon=True).start()

            # kirim pesan ke client ini
            while True:
                message = q.get()
                yield message

        except Exception as e:
            print("Client error:", e)

        finally:
            # cleanup
            with lock:
                if user_room in clients and username in clients[user_room]:
                    del clients[user_room][username]
                    print(f"{username} left {user_room}")

                # hapus room kalau kosong
                if user_room in clients and not clients[user_room]:
                    del clients[user_room]
                    print(f"{user_room} deleted (empty)")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    print("Chat Server running on port 50051...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()