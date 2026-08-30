import paho.mqtt.client as mqtt

BROKER = "8.137.105.88"
PORT = 1883
TOPIC = "sensor/+/data"


def on_connect(client, userdata, flags, rc):
    print("已连接 EMQX，rc =", rc)
    client.subscribe(TOPIC)
    print("已订阅主题:", TOPIC)


def on_message(client, userdata, msg):
    print("[" + msg.topic + "] " + msg.payload.decode("utf-8"))


client = mqtt.Client(client_id="verify-sub")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
print("开始监听，按 Ctrl+C 退出...")
client.loop_forever()
