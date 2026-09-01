"""本地 MQTT 模拟设备：上报温湿度、心跳，并回传灌溉执行结果。"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import random
import time

import paho.mqtt.client as mqtt


BROKER_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL_SECONDS = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "5"))

# 与 database/seed/03_devices.sql 保持一致。
SENSORS = (
    {"deviceNo": "GH01-SOIL-001", "deviceId": "device_001", "type": "humidity", "range": (28.0, 48.0)},
    {"deviceNo": "GH01-TEMP-001", "deviceId": "device_002", "type": "temperature", "range": (20.0, 32.0)},
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def publish_status(client: mqtt.Client, device_id: str) -> None:
    client.publish(
        f"farm/status/{device_id}",
        json.dumps({"deviceId": device_id, "online": True, "ts": now()}),
        qos=1,
    )


def on_connect(client: mqtt.Client, userdata: object, flags: object, reason_code: object, properties: object = None) -> None:
    print(f"Connected to MQTT broker {BROKER_HOST}:{BROKER_PORT}")
    client.subscribe("farm/command/device_003", qos=1)
    for sensor in SENSORS:
        publish_status(client, sensor["deviceId"])
    publish_status(client, "device_003")


def on_message(client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
    """灌溉控制器接收命令后模拟执行成功，并按约定回传。"""
    try:
        command = json.loads(message.payload.decode("utf-8"))
        if command.get("action") not in {"irrigation_on", "irrigation_off"}:
            raise ValueError("unsupported action")
        response = {
            "commandId": command["commandId"], "deviceId": "device_003",
            "result": "success", "ts": now(),
        }
        client.publish("farm/command_result/device_003", json.dumps(response), qos=1)
        print(f"Command complete: {response}")
    except (json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"Ignored invalid command: {error}")


def main() -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="smart-farm-simulator")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    sequence = 0
    try:
        while True:
            sequence += 1
            for sensor in SENSORS:
                value = round(random.uniform(*sensor["range"]), 2)
                report = {
                    **{key: sensor[key] for key in ("deviceNo", "deviceId", "type")},
                    "value": value, "msgId": f"SIM-{sensor['deviceId']}-{sequence}", "ts": now(),
                }
                client.publish(f"farm/telemetry/{sensor['deviceId']}", json.dumps(report), qos=1)
                publish_status(client, sensor["deviceId"])
                print(f"Telemetry: {report}")
            publish_status(client, "device_003")
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Simulator stopped")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
