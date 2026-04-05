import grpc
from concurrent import futures
import time
import queue

import chat_pb2
import chat_pb2_grpc

clients = []

class ChatService(chat_pb2_grpc.ChatServiceServicer):

    def ChatStream(self, request_iterator, context):
        print("Client connected")

        q = queue.Queue()
        clients.append(q)

        try:
            # thread untuk menerima pesan dari client ini
            def receive_messages():
                for message in request_iterator:
                    print(f"{message.username}: {message.message}")

                    # broadcast ke semua client
                    for client_queue in clients:
                        client_queue.put(message)

            import threading
            threading.Thread(target=receive_messages, daemon=True).start()

            # kirim pesan ke client ini
            while True:
                message = q.get()
                yield message

        except:
            print("Client disconnected")
            clients.remove(q)


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