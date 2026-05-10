import time
import json
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Daftar command bot
def process_bot_command(command, user_id):
    command = command.lower().strip()
    if command == "help":
        return "Perintah tersedia: help, ping, time"
    elif command == "ping":
        return "Pong!"
    elif command == "time":
        from datetime import datetime
        return f"Waktu server: {datetime.now().strftime('%H:%M:%S')}"
    else:
        return f"Perintah '{command}' tidak dikenal."

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[ChatWorker] Terhubung ke MQTT Broker!")
        
        # Subscribe ke shared subscription untuk analitik/log
        # $share/chat_workers/chat/room/# 
        # (Orang 2 - Wildcard & Shared Subscription)
        client.subscribe("$share/chat_workers/chat/room/#", qos=1)
        print("[ChatWorker] Subscribed to shared topic: $share/chat_workers/chat/room/#")
        
        # Subscribe ke topic request-response untuk bot
        # (Orang 3 - Request-Response)
        client.subscribe("chat/request/bot", qos=1)
        print("[ChatWorker] Subscribed to request topic: chat/request/bot")
    else:
        print(f"[ChatWorker] Gagal connect MQTT, rc={rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    
    try:
        # Analitik & Log (Dari shared subscription)
        if topic.startswith("chat/room/"):
            room = topic.split("/")[-1]
            payload = json.loads(msg.payload.decode())
            
            # Abaikan pesan 'typing' atau 'join' agar log tidak terlalu penuh
            msg_type = payload.get("type", "message")
            if msg_type == "message":
                username = payload.get("username", "Unknown")
                text = payload.get("message", "")
                print(f"[Analytic Log] Room: {room} | {username}: {text}")

        # Request-Response Bot
        elif topic == "chat/request/bot":
            payload = json.loads(msg.payload.decode())
            command = payload.get("command", "")
            user_id = payload.get("user_id", "Unknown")
            
            print(f"[ChatWorker] Menerima request bot dari {user_id}: {command}")
            
            # Cek ResponseTopic dari properti (MQTTv5)
            props = getattr(msg, "properties", None)
            if props and hasattr(props, "ResponseTopic") and props.ResponseTopic:
                response_topic = props.ResponseTopic
                response_text = process_bot_command(command, user_id)
                
                # Kirim balasan ke ResponseTopic
                reply_payload = json.dumps({
                    "message": f"🤖 Bot: {response_text}",
                    "type": "bot_response"
                })
                client.publish(response_topic, reply_payload, qos=1)
                print(f"[ChatWorker] Mengirim balasan bot ke {response_topic}")
            else:
                print(f"[ChatWorker] Peringatan: Tidak ada ResponseTopic dari {user_id}")
                
    except Exception as e:
        print(f"[ChatWorker] Error processing message: {e}")

def serve():
    print("========================================")
    print("🚀 Memulai ChatWorker (MQTT Daemon)...")
    print("========================================")
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
    
    # Konfigurasi Receive Maximum (Orang 3 - Flow Control / Backpressure)
    # Membatasi jumlah pesan unacknowledged untuk mensimulasikan backpressure
    connect_props = Properties(PacketTypes.CONNECT)
    connect_props.ReceiveMaximum = 10  # Maksimal 10 pesan sebelum di-acknowledge
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60, properties=connect_props)
        client.loop_forever()
    except Exception as e:
        print(f"[ChatWorker] Terjadi kesalahan: {e}")

if __name__ == "__main__":
    serve()