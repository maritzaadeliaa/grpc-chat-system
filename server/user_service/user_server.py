import grpc
from concurrent import futures
import time

import user_pb2
import user_pb2_grpc

active_users = set()

class UserService(user_pb2_grpc.UserServiceServicer):

    def Login(self, request, context):
        username = request.username

        if not username:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Username kosong")

        if username in active_users:
            return user_pb2.UserResponse(
                status="FAIL",
                message="Username already taken"
            )

        active_users.add(username)

        return user_pb2.UserResponse(
            status="SUCCESS",
            message=f"{username} logged in"
        )

    def Logout(self, request, context):
        username = request.username
        if username in active_users:
            active_users.remove(username)
        return user_pb2.UserResponse(
            status="SUCCESS",
            message=f"{username} logged out"
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)

    server.add_insecure_port('[::]:50052')
    server.start()
    print("User Server running on port 50052...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()