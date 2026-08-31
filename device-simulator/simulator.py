from __future__ import annotations

import argparse
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

TEMP_UUID = "3b8dcefd-3a51-4adc-b452-47c184c0951d"
MOIST_UUID = "814621f7-2561-49ad-9766-72d3fcd18d86"
IRRIG_UUID = "435106ba-01e7-4745-9646-3907d15b28df"


def timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def publish(client: mqtt.Client, topic: str, payload: dict[str, object]) -> None:
    result = client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
    result.wait_for_publish()


def publish_state(client: mqtt.Client, device_id: str, switch: str, *, reason: str = "heartbeat") -> None:
    now = timestamp_ms()
    publish(client, "sensor/state", {"seq": now, "ts": now, "deviceId": device_id, "switch": switch, "reason": reason, "values": {}})


def publish_telemetry(client: mqtt.Client, moisture: float, temperature: float = 25.6) -> None:
    now = timestamp_ms()
    publish(client, f"sensor/{TEMP_UUID}/data", {"temperature": round(temperature, 2), "deviceId": TEMP_UUID, "timestamp": now, "msgId": str(now)})
    time.sleep(0.02)
    now = timestamp_ms()
    publish(client, f"sensor/{MOIST_UUID}/data", {"plot_moisture": round(moisture, 2), "deviceId": MOIST_UUID, "timestamp": now, "msgId": str(now)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart-farm MQTT telemetry publisher")
    parser.add_argument("--once", action="store_true", help="Publish one telemetry pair")
    parser.add_argument("--interval", type=float, default=5, help="Seconds between telemetry reports")
    parser.add_argument("--moisture", type=float, default=40, help="Fixed soil-moisture value to report")
    args = parser.parse_args()
    if args.interval <= 0 or not 0 <= args.moisture <= 100:
        parser.error("interval must be positive and moisture must be between 0 and 100")

    state: dict[str, object] = {"irrigation": False}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"farm-simulator-{os.getpid()}")

    def on_connect(active_client: mqtt.Client, _userdata: object, _flags: object, reason_code: object, _properties: object) -> None:
        if int(reason_code) == 0:
            active_client.subscribe("sensor/cmd", qos=1)

    def on_message(active_client: mqtt.Client, _userdata: object, message: mqtt.MQTTMessage) -> None:
        try:
            command = json.loads(message.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if command.get("deviceId") != IRRIG_UUID or command.get("switch") not in {"on", "off"}:
            return
        switch = command["switch"]
        state["irrigation"] = switch == "on"
        now = timestamp_ms()
        publish(active_client, "sensor/ack", {"seq": now, "cmdSeq": command.get("seq"), "action": "control", "deviceId": IRRIG_UUID, "result": "ok", "switch": switch, "name": "P001-IRRIG"})
        publish_state(active_client, IRRIG_UUID, switch, reason="remote")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(os.getenv("MQTT_HOST", "127.0.0.1"), int(os.getenv("MQTT_PORT", "1883")), keepalive=60)
    client.loop_start()
    for device_id, switch in ((TEMP_UUID, "on"), (MOIST_UUID, "on"), (IRRIG_UUID, "off")):
        publish_state(client, device_id, switch)

    try:
        while True:
            publish_telemetry(client, float(args.moisture))
            print(f"moisture={args.moisture:.2f}% irrigation={'on' if state['irrigation'] else 'off'}")
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
