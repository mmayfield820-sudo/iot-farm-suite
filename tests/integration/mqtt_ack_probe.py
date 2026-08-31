"""One-shot MQTT device probe for the Stage 0 control/ACK baseline test.

This is a protocol test double, not a replacement for the HarmonyOS simulator.
It acknowledges the first control command addressed to the configured device UUID.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-uuid", required=True)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    acknowledged = False
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"stage0-ack-{os.getpid()}")

    def on_connect(connected: mqtt.Client, _userdata, _flags, reason_code, _properties) -> None:
        if reason_code != 0:
            raise RuntimeError(f"MQTT connection failed: {reason_code}")
        connected.subscribe("sensor/cmd", qos=1)
        print("MQTT_CONNECTED", flush=True)

    def on_message(connected: mqtt.Client, _userdata, message) -> None:
        nonlocal acknowledged
        payload = json.loads(message.payload.decode("utf-8"))
        print(f"COMMAND_RECEIVED action={payload.get('action')} deviceId={payload.get('deviceId')}", flush=True)
        # The current backend control payload is identified by deviceId + switch;
        # the simulator returns action=control in its ACK.
        if payload.get("deviceId") != args.device_uuid or payload.get("switch") not in {"on", "off"}:
            return
        now = int(time.time() * 1000)
        ack = {
            "seq": now,
            "cmdSeq": payload["seq"],
            "action": "control",
            "result": "ok",
            "deviceId": args.device_uuid,
            "switch": payload["switch"],
        }
        connected.publish("sensor/ack", json.dumps(ack), qos=1)
        acknowledged = True

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(os.getenv("MQTT_HOST", "127.0.0.1"), int(os.getenv("MQTT_PORT", "1883")), 30)
    client.loop_start()
    deadline = time.monotonic() + args.timeout
    while not acknowledged and time.monotonic() < deadline:
        time.sleep(0.1)
    if acknowledged:
        time.sleep(1)
    client.loop_stop()
    client.disconnect()
    if not acknowledged:
        raise TimeoutError("No matching control command received")
    print("ACK_PUBLISHED")


if __name__ == "__main__":
    main()
