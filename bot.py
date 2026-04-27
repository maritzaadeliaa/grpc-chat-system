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
    
    # Salam pembuka
    initial_msgs = ["Halo! Saya bot siap membantu.", "Bot hadir!", "Selamat datang semuanya."]
    send_queue.put(chat_pb2.ChatMessage(username=username, room=room, message=random.choice(initial_msgs), msg_type="chat"))
    
    def stream_messages():
        while True:
            yield send_queue.get()

    try:
        responses = stub.ChatStream(stream_messages())
        for response in responses:
            # JANGAN membalas jika pesan berasal dari bot lain (agar tidak looping)
            if response.username.startswith("Bot_") or response.username == username:
                continue

            # Logika Balas Chat Sederhana
            msg_lower = response.message.lower()
            reply = ""

            if "halo" in msg_lower or "hi" in msg_lower:
                reply = f"Halo juga {response.username}! Senang melihatmu di sini."
            elif "ping" in msg_lower:
                reply = "Pong! Koneksi gRPC dari bot sangat stabil."
            elif "tugas" in msg_lower:
                reply = "Semangat ngerjain tugas Week 9-nya! Kamu pasti bisa dapat A."
            elif "siapa" in msg_lower:
                reply = f"Saya adalah Bot nomor {bot_id}, asisten virtual untuk demo gRPC ini."
            elif "keren" in msg_lower or "mantap" in msg_lower:
                reply = "Terima kasih! Ini semua berkat integrasi gRPC dan WebSocket."

            if reply:
                # Beri jeda sedikit agar terlihat natural seperti mengetik
                time.sleep(random.uniform(1.0, 2.5))
                send_queue.put(chat_pb2.ChatMessage(
                    username=username,
                    room=room,
                    message=reply,
                    msg_type="chat"
                ))

    except Exception as e:
        print(f"[{username}] Terputus: {e}")

if __name__ == "__main__":
    num_bots = 1
    target_room = "umum"

    if len(sys.argv) > 1:
        try:
            num_bots = int(sys.argv[1])
        except ValueError: pass
    
    if len(sys.argv) > 2:
        target_room = sys.argv[2]

    print(f"--- Menjalankan {num_bots} Bot Interaktif di room '{target_room}' ---")
    print("Bot akan merespon kata: 'halo', 'ping', 'tugas', 'siapa', 'keren'")
    
    for i in range(1, num_bots + 1):
        threading.Thread(target=chat_bot, args=(i, target_room), daemon=True).start()
        time.sleep(0.3)

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Semua bot dimatikan ---")
