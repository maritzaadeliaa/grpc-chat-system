import grpc

import user_pb2
import user_pb2_grpc

import room_pb2
import room_pb2_grpc

import chat_pb2
import chat_pb2_grpc


def run():
    username = input("Username: ")
    room = input("Room: ")

    # USER SERVICE
    user_channel = grpc.insecure_channel('localhost:50052')
    user_stub = user_pb2_grpc.UserServiceStub(user_channel)

    res = user_stub.Login(user_pb2.UserRequest(username=username))
    print(res.message)

    if res.status != "SUCCESS":
        return

    # ROOM SERVICE
    room_channel = grpc.insecure_channel('localhost:50053')
    room_stub = room_pb2_grpc.RoomServiceStub(room_channel)

    res = room_stub.JoinRoom(room_pb2.RoomRequest(username=username, room=room))
    print(res.message)

    # CHAT SERVICE
    chat_channel = grpc.insecure_channel('localhost:50051')
    chat_stub = chat_pb2_grpc.ChatServiceStub(chat_channel)

    # ✅ generator untuk kirim pesan
    def generate_messages():
        while True:
            msg = input(">> ")
            yield chat_pb2.ChatMessage(
                username=username,
                room=room,
                message=msg
            )

    # streaming
    responses = chat_stub.ChatStream(generate_messages())

    # receive
    try:
        for response in responses:
            print(f"{response.username}: {response.message}")
    except:
        print("Disconnected from server")


if __name__ == '__main__':
    run()