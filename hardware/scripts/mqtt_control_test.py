import json
import time
import paho.mqtt.client as mqtt

BROKER = "8.137.105.88"
PORT = 1883
TOPIC_CMD = "sensor/cmd"
TOPIC_ACK = "sensor/ack"

IRRIG_UUID = "435106ba-01e7-4745-9646-3907d15b28df"

acks = []


def on_connect(client, userdata, flags, rc):
    print("connected rc =", rc)
    client.subscribe(TOPIC_ACK)
    print("已订阅:", TOPIC_ACK)


def on_message(client, userdata, msg):
    line = msg.payload.decode("utf-8")
    print("[收到] " + line)
    acks.append(line)


def send_cmd(client, seq, switch):
    ts = int(time.time() * 1000)
    payload = json.dumps({
        "seq": seq,
        "ts": ts,
        "deviceId": IRRIG_UUID,
        "switch": switch,
    })
    print("[发送] sensor/cmd <-", payload)
    client.publish(TOPIC_CMD, payload, qos=1)


client = mqtt.Client(client_id="ctrl-test")
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

time.sleep(1)  # 等订阅建立

# 开马达
send_cmd(client, 10001, "on")
time.sleep(5)

# 关马达
send_cmd(client, 10002, "off")
time.sleep(5)

client.loop_stop()
client.disconnect()

print("---")
print(f"收到 {len(acks)} 条回执")
for a in acks:
    print(" ", a)
