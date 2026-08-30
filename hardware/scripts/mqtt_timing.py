import time
import paho.mqtt.client as mqtt

BROKER = "8.137.105.88"
PORT = 1883
TOPIC = "sensor/+/data"
WINDOW = 60

arrivals = []  # (t_seconds, topic)

t0 = time.time()


def on_connect(client, userdata, flags, rc):
    print("connected rc =", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    arrivals.append((round(time.time() - t0, 1), msg.topic.split("/")[1][:8]))


client = mqtt.Client(client_id="verify-timing")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

time.sleep(WINDOW)
client.loop_stop()
client.disconnect()

print(f"--- {WINDOW} 秒内收到 {len(arrivals)} 条 ---")
for t, dev in arrivals:
    print(f"  +{t:6.1f}s  {dev}")

if arrivals:
    times = [a[0] for a in arrivals]
    gaps = [round(times[i+1] - times[i], 1) for i in range(len(times) - 1)]
    print("相邻消息间隔(秒):", gaps)
