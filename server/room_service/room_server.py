import grpc
from concurrent import futures
import time

import room_pb2
import room_pb2_grpc

rooms = {}

class RoomService(room_pb2_grpc.RoomServiceServicer):

    def JoinRoom(self, request, context):
        username = request.username
        room = request.room

        if room not in rooms:
            rooms[room] = []

        if username not in rooms[room]:
            rooms[room].append(username)

        return room_pb2.RoomResponse(
            status="SUCCESS",
            message=f"{username} joined {room}"
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    room_pb2_grpc.add_RoomServiceServicer_to_server(RoomService(), server)

    server.add_insecure_port('[::]:50053')
    server.start()
    print("Room Server running on port 50053...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()