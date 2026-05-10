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
    
    channel = grpc.insecure_channel('localhost:50054')
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    import queue
    send_queue = queue.Queue()
    
    # Daftarkan bot
    send_queue.put(chat_pb2.ChatMessage(username=username, room=room, msg_type="join"))
    time.sleep(random.uniform(0.5, 2.0))
    
    responses_dict = {
        "halo": [
            f"Halo juga! Salam kenal ya.",
            f"Hi! Senang melihatmu aktif di sini.",
            f"Oit! Apa kabar?",
            f"Halo, saya Bot siap membantu!"
        ],
        "tugas": [
            "Semangat ngerjain tugasnya! Kamu pasti bisa.",
            "Tugas Week 9 emang seru ya, apalagi pakai gRPC.",
            "Jangan lupa istirahat kalau udah capek ngerjain tugas.",
            "Butuh bantuan buat tugas? Tanya aja ke asisten dosen hehe."
        ],
        "ping": [
            "Pong! Koneksi aman terkendali.",
            "Ping received! Latency sangat rendah nih.",
            "Hadir! gRPC stream lancar jaya.",
            "Pong! Semua service online."
        ],
        "keren": [
            "Mantap kan? Integrasi sistem emang asik.",
            "Makasih! Tim pengembangnya hebat nih.",
            "Yoi! Teknologi gRPC emang masa depan.",
            "Setuju! Web UI-nya juga estetik banget."
        ]
    }

    def stream_messages():
        while True:
            yield send_queue.get()

    try:
        responses = stub.ChatStream(stream_messages())
        for response in responses:
            if response.username.startswith("Bot_") or response.username == username:
                continue

            # Probabilitas membalas (70% biar tidak semua bot nyaut barengan)
            if random.random() > 0.7:
                continue

            msg_lower = response.message.lower()
            reply_text = ""

            for key, variations in responses_dict.items():
                if key in msg_lower:
                    reply_text = random.choice(variations).format(response.username)
                    break
            
            if "siapa" in msg_lower:
                reply_text = f"Saya Bot_{bot_id}. Saya di sini untuk menemani kamu di room {room}."

            if reply_text:
                # Simulasi waktu mengetik
                time.sleep(random.uniform(1.0, 3.0))
                send_queue.put(chat_pb2.ChatMessage(
                    username=username, room=room, message=reply_text, msg_type="chat"
                ))

    except Exception as e:
        print(f"[{username}] Terputus: {e}")

if __name__ == "__main__":
    num_bots = 1
    target_room = "umum"

    if len(sys.argv) > 1:
        try: num_bots = int(sys.argv[1])
        except ValueError: pass
    
    if len(sys.argv) > 2: target_room = sys.argv[2]

    print(f"--- Menjalankan {num_bots} Bot Variatif di room '{target_room}' ---")
    
    for i in range(1, num_bots + 1):
        threading.Thread(target=chat_bot, args=(i, target_room), daemon=True).start()
        time.sleep(0.3)

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Semua bot dimatikan ---")
