import grpc
import time
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import chat_pb2 as chat_pb2
import chat_pb2_grpc as chat_pb2_grpc

def chat_bot(username="system_bot", room="umum"):
    print(f"[{username}] Start connecting to room '{room}'...")
    
    channel = grpc.insecure_channel('localhost:50054')
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    # Queue for messages to send
    import queue
    send_queue = queue.Queue()
    
    # Send join message immediately to register
    send_queue.put(chat_pb2.ChatMessage(
        username=username,
        room=room,
        msg_type="join"
    ))
    
    # Send a greeting message
    time.sleep(1)
    send_queue.put(chat_pb2.ChatMessage(
        username=username,
        room=room,
        message="Halo! Saya System Bot. Ketik /help untuk melihat daftar perintah.",
        msg_type="message"
    ))

    def msg_generator():
        while True:
            msg = send_queue.get()
            if msg is None:
                break
            # set timestamp
            from datetime import datetime
            msg.timestamp = datetime.now().strftime("%H:%M:%S")
            yield msg

    def process_responses():
        try:
            for response in stub.ChatStream(msg_generator()):
                if response.msg_type in ("typing", "join"):
                    continue
                
                # Ignore my own messages
                if response.username == username:
                    continue
                
                text = response.message.strip()
                
                # Profanity filter placeholder
                bad_words = ["jelek", "bodoh", "kasar"]
                for w in bad_words:
                    if w in text.lower():
                        send_queue.put(chat_pb2.ChatMessage(
                            username=username,
                            room=room,
                            message=f"@{response.username} Tolong jaga bahasa Anda di room ini!",
                            msg_type="message"
                        ))
                        break

                # Commands
                if text.startswith("/help"):
                    send_queue.put(chat_pb2.ChatMessage(
                        username=username,
                        room=room,
                        message="Daftar perintah:\n/help - Menampilkan pesan ini\n/cuaca - Cek cuaca hari ini\n/waktu - Cek waktu server",
                        msg_type="message"
                    ))
                elif text.startswith("/cuaca"):
                    send_queue.put(chat_pb2.ChatMessage(
                        username=username,
                        room=room,
                        message="☔ Perkiraan cuaca: Hujan deras algoritma di server ini.",
                        msg_type="message"
                    ))
                elif text.startswith("/waktu"):
                    from datetime import datetime
                    send_queue.put(chat_pb2.ChatMessage(
                        username=username,
                        room=room,
                        message=f"🕒 Waktu server saat ini: {datetime.now().strftime('%H:%M:%S')}",
                        msg_type="message"
                    ))
        except grpc.RpcError as e:
            print(f"[{username}] Kesalahan gRPC: {e.details()}")
        except Exception as e:
            print(f"[{username}] Terjadi kesalahan: {e}")

    try:
        process_responses()
    except KeyboardInterrupt:
        print(f"[{username}] Bot dimatikan.")
        send_queue.put(None)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jalankan System Bot gRPC")
    parser.add_argument("--room", default="umum", help="Nama room yang akan dijaga")
    parser.add_argument("--name", default="system_bot", help="Nama bot")
    args = parser.parse_args()
    
    chat_bot(args.name, args.room)
