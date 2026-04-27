import grpc
import chat_pb2 as chat_pb2
import chat_pb2_grpc as chat_pb2_grpc
import time
import threading
import sys
import os
import random

def chat_bot(bot_id, room="umum"):
    username = f"Bot_{bot_id}"
    print(f"[{username}] Memulai koneksi ke room '{room}'...")
    
    # Gunakan port 50054 sesuai konfigurasi Chat Service terbaru
    channel = grpc.insecure_channel('localhost:50054')
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    import queue
    send_queue = queue.Queue()
    
    # Daftarkan bot ke room
    send_queue.put(chat_pb2.ChatMessage(
        username=username,
        room=room,
        msg_type="join"
    ))
    
    # Beri jeda sedikit agar bot tidak masuk berbarengan
    time.sleep(random.uniform(0.5, 2.0))
    
    # Kirim pesan salam
    greetings = [
        "Halo semua! Saya di sini untuk meramaikan room.",
        "Semangat belajarnya ya!",
        "Sistem integrasi gRPC ini keren sekali!",
        "Ada yang bisa saya bantu?",
        "Selamat datang di room umum!"
    ]
    
    send_queue.put(chat_pb2.ChatMessage(
        username=username,
        room=room,
        message=random.choice(greetings),
        msg_type="chat"
    ))
    
    def stream_messages():
        while True:
            msg = send_queue.get()
            yield msg

    try:
        # Mulai stream chat
        responses = stub.ChatStream(stream_messages())
        for response in responses:
            # Bot hanya mendengarkan, tidak perlu merespon agar tidak loop chat
            pass
    except grpc.RpcError as e:
        print(f"[{username}] Koneksi terputus: {e}")
    except Exception as e:
        print(f"[{username}] Error: {e}")

if __name__ == "__main__":
    # Default: jalankan 1 bot
    num_bots = 1
    target_room = "umum"

    if len(sys.argv) > 1:
        try:
            num_bots = int(sys.argv[1])
        except ValueError:
            print("Penggunaan: python bot.py [jumlah_bot] [nama_room]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        target_room = sys.argv[2]

    print(f"--- Menjalankan {num_bots} bot di room '{target_room}' ---")
    
    threads = []
    for i in range(1, num_bots + 1):
        t = threading.Thread(target=chat_bot, args=(i, target_room), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.3) # Jeda antar bot join

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Semua bot dimatikan ---")
