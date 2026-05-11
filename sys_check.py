import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe("$SYS/#")
    print("Connected, subscribing to $SYS/#")

def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_connect = on_connect
c.on_message = on_message
c.connect("localhost")
c.loop_start()
time.sleep(3)
c.disconnect()
