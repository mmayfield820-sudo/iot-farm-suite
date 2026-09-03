from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from backend.app.mqtt import MqttService


class MqttTimestampTests(unittest.TestCase):
    def test_default_client_id_is_unique_to_the_backend_process(self):
        with (
            patch.dict("os.environ", {"MQTT_CLIENT_ID": ""}),
            patch("backend.app.mqtt.socket.gethostname", return_value="farm-host"),
            patch("backend.app.mqtt.os.getpid", return_value=1234),
        ):
            service = MqttService()

        self.assertEqual(service.client_id, "smart-farm-backend-farm-host-1234")

    def test_configured_client_id_is_preserved(self):
        with patch.dict("os.environ", {"MQTT_CLIENT_ID": "backend-p001"}):
            service = MqttService()

        self.assertEqual(service.client_id, "backend-p001")

    def test_device_uptime_uses_backend_receive_time(self):
        received_at = datetime(2026, 9, 3, 12, 0, 0)

        timestamp = MqttService._parse_device_timestamp(71710, received_at)

        self.assertEqual(timestamp, received_at)

    def test_unix_milliseconds_are_preserved(self):
        received_at = datetime(2026, 9, 3, 12, 0, 0)

        timestamp = MqttService._parse_device_timestamp(1788436800000, received_at)

        self.assertEqual(timestamp, datetime(2026, 9, 3, 12, 0, 0))

    def test_non_positive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timestamp must be positive"):
            MqttService._parse_device_timestamp(0, datetime(2026, 9, 3))


if __name__ == "__main__":
    unittest.main()
