from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from datetime import UTC, datetime

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def publish(client: mqtt.Client, topic: str, payload: dict[str, object]) -> None:
    result = client.publish(topic, json.dumps(payload), qos=1)
    result.wait_for_publish()


def timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish demo smart-farm MQTT data")
    parser.add_argument("--once", action="store_true", help="Publish one telemetry pair")
    args = parser.parse_args()

    host = os.getenv("MQTT_HOST", "127.0.0.1")
    port = int(os.getenv("MQTT_PORT", "1883"))
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="farm-simulator")
    client.connect(host, port, keepalive=60)
    client.loop_start()

    devices = [
        ("P001-TEMP", "3b8dcefd-3a51-4adc-b452-47c184c0951d", "on"),
        ("P001-MOIST", "814621f7-2561-49ad-9766-72d3fcd18d86", "on"),
        ("P001-IRRIG", "435106ba-01e7-4745-9646-3907d15b28df", "off"),
    ]
    for device_no, device_id, switch in devices:
        now = timestamp_ms()
        publish(
            client,
            "sensor/state",
            {
                "seq": now,
                "ts": now,
                "deviceId": device_id,
                "switch": switch,
                "reason": "heartbeat",
                "values": {},
            },
        )

    while True:
        now = timestamp_ms()
        publish(
            client,
            "sensor/3b8dcefd-3a51-4adc-b452-47c184c0951d/data",
            {
                "temperature": 25.6,
                "deviceId": "3b8dcefd-3a51-4adc-b452-47c184c0951d",
                "timestamp": now,
                "msgId": str(now),
            },
        )
        now = timestamp_ms()
        publish(
            client,
            "sensor/814621f7-2561-49ad-9766-72d3fcd18d86/data",
            {
                "plot_moisture": 62.5,
                "deviceId": "814621f7-2561-49ad-9766-72d3fcd18d86",
                "timestamp": now,
                "msgId": str(now),
            },
        )
        if args.once:
            break
        time.sleep(10)

    time.sleep(1)
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
