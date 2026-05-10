import grpc
import chat_pb2
import chat_pb2_grpc
import time

def test_chat():
    channel = grpc.insecure_channel('localhost:50051')
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    def gen():
        yield chat_pb2.ChatMessage(username="tester", room="test", msg_type="join")
        time.sleep(1)
        yield chat_pb2.ChatMessage(username="tester", room="test", message="ping", msg_type="message")
        time.sleep(1)

    try:
        for resp in stub.ChatStream(gen()):
            print(f"Received: {resp.username}: {resp.message} ({resp.msg_type})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
