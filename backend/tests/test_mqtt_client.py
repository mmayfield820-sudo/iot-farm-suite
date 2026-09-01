"""MQTT 实际消息处理测试。"""

import unittest
from unittest.mock import MagicMock

from src.mqtt.client import SmartFarmMqttClient


class MqttClientTest(unittest.TestCase):
    """验证 MQTT 客户端能够解析遥测主题消息。"""

    def test_handle_telemetry_message_parses_json_and_device_id(self) -> None:
        handler = MagicMock()
        handler.handle.return_value = {"kind": "telemetry", "accepted": True, "duplicate": False}
        client = SmartFarmMqttClient(handler=handler)
        message = {
            "deviceNo": "SENSOR-001",
            "deviceId": "device_001",
            "type": "temperature",
            "value": 25.6,
            "msgId": "M00001",
            "ts": "2026-08-30T10:00:00",
        }

        result = client.handle_message("farm/telemetry/device_001", message)

        self.assertEqual(result["deviceId"], "device_001")
        self.assertEqual(result["type"], "temperature")
        self.assertEqual(result["value"], 25.6)
        self.assertTrue(result["accepted"])
        self.assertEqual(client.last_message["topic"], "farm/telemetry/device_001")
        handler.handle.assert_called_once_with("farm/telemetry/device_001", message)


if __name__ == "__main__":
    unittest.main()
