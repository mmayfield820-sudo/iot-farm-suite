"""MQTT 入站消息的业务校验测试。"""

import unittest
from unittest.mock import MagicMock

from src.mqtt.message_handler import MqttMessageHandler


class MqttMessageHandlerTest(unittest.TestCase):
    def test_rejects_topic_and_payload_device_id_mismatch(self) -> None:
        handler = MqttMessageHandler(MagicMock())

        with self.assertRaisesRegex(ValueError, "不一致"):
            handler.handle(
                "farm/status/device_001",
                {"deviceId": "device_002", "online": True, "ts": "2026-08-31T10:00:00"},
            )

    def test_rejects_invalid_humidity_before_database_write(self) -> None:
        engine = MagicMock()
        handler = MqttMessageHandler(engine)

        with self.assertRaisesRegex(ValueError, "0 到 100"):
            handler.handle(
                "farm/telemetry/device_001",
                {
                    "deviceId": "device_001", "type": "humidity", "value": 101,
                    "msgId": "M00001", "ts": "2026-08-31T10:00:00",
                },
            )
        engine.begin.assert_not_called()


if __name__ == "__main__":
    unittest.main()
