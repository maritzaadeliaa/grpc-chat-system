import grpc
from concurrent import futures
import time
import sys
import os

# Fix import path - add root project directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import room_pb2
import room_pb2_grpc

# In-memory storage: room_name -> list of usernames
rooms = {}

class RoomService(room_pb2_grpc.RoomServiceServicer):

    def JoinRoom(self, request, context):
        username = request.username.strip()
        room = request.room.strip()

        if not username or not room:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Username dan room tidak boleh kosong")
            return

        if room not in rooms:
            rooms[room] = []

        if username not in rooms[room]:
            rooms[room].append(username)

        print(f"[RoomService] {username} joined '{room}'. Members: {rooms[room]}")

        return room_pb2.RoomResponse(
            status="SUCCESS",
            message=f"{username} berhasil bergabung ke room '{room}'"
        )

    def LeaveRoom(self, request, context):
        username = request.username.strip()
        room = request.room.strip()

        if room in rooms and username in rooms[room]:
            rooms[room].remove(username)
            print(f"[RoomService] {username} left '{room}'. Members: {rooms.get(room, [])}")

            # Hapus room kalau sudah kosong
            if not rooms[room]:
                del rooms[room]
                print(f"[RoomService] Room '{room}' deleted (empty)")

        return room_pb2.RoomResponse(
            status="SUCCESS",
            message=f"{username} berhasil keluar dari room '{room}'"
        )

    def GetRoomMembers(self, request, context):
        room = request.room.strip()
        members = rooms.get(room, [])

        return room_pb2.RoomResponse(
            status="SUCCESS",
            message=",".join(members)
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    room_pb2_grpc.add_RoomServiceServicer_to_server(RoomService(), server)

    server.add_insecure_port('[::]:50053')
    server.start()
    print("=" * 40)
    print("[OK] Room Server running on port 50053")
    print("=" * 40)

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        print("\n[RoomService] Server stopped.")


if __name__ == '__main__':
    serve()