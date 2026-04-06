import grpc
from concurrent import futures
import time
import sys
import os

# Fix import path - add root project directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import user_pb2
import user_pb2_grpc

# In-memory "database" untuk user yang aktif
active_users = set()

class UserService(user_pb2_grpc.UserServiceServicer):

    def Login(self, request, context):
        username = request.username.strip()

        if not username:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Username tidak boleh kosong")
            return

        if username in active_users:
            return user_pb2.UserResponse(
                status="FAIL",
                message=f"Username '{username}' sudah dipakai orang lain"
            )

        active_users.add(username)
        print(f"[UserService] {username} login berhasil. Active users: {list(active_users)}")

        return user_pb2.UserResponse(
            status="SUCCESS",
            message=f"{username} berhasil login"
        )

    def Logout(self, request, context):
        username = request.username.strip()

        if username in active_users:
            active_users.discard(username)
            print(f"[UserService] {username} logout. Active users: {list(active_users)}")
            return user_pb2.UserResponse(
                status="SUCCESS",
                message=f"{username} berhasil logout"
            )

        return user_pb2.UserResponse(
            status="FAIL",
            message=f"Username '{username}' tidak ditemukan"
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    server.add_insecure_port('[::]:50052')
    server.start()
    print("=" * 40)
    print("[OK] User Server running on port 50052")
    print("=" * 40)

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        print("\n[UserService] Server stopped.")


if __name__ == '__main__':
    serve()