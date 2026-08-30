import time
import paho.mqtt.client as mqtt

BROKER = "8.137.105.88"
PORT = 1883
TOPIC = "sensor/+/data"
WINDOW = 30

temp = []
moist = []


def on_connect(client, userdata, flags, rc):
    print("connected rc =", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    import json
    try:
        j = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return
    if "temperature" in j:
        temp.append(j["temperature"])
    if "plot_moisture" in j:
        moist.append(j["plot_moisture"])


client = mqtt.Client(client_id="verify-measure")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

time.sleep(WINDOW)

client.loop_stop()
client.disconnect()

print("---")
print(f"{WINDOW}秒内收到: 温度 {len(temp)} 条, 湿度 {len(moist)} 条")
print("温度样例:", temp[:5])
print("湿度样例:", moist[:5])
