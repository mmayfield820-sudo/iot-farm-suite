import time
import paho.mqtt.client as mqtt

BROKER = "8.137.105.88"
PORT = 1883
TOPIC = "sensor/+/data"

msgs = []


def on_connect(client, userdata, flags, rc):
    print("connected rc =", rc)
    client.subscribe(TOPIC)
    print("subscribed:", TOPIC)


def on_message(client, userdata, msg):
    line = "[" + msg.topic + "] " + msg.payload.decode("utf-8")
    print(line)
    msgs.append(line)


client = mqtt.Client(client_id="verify-once")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

time.sleep(12)

client.loop_stop()
client.disconnect()
print("---")
print("12秒内共收到", len(msgs), "条消息")
