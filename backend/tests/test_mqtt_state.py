from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.app.mqtt import MqttService


IRRIGATION_UUID = "435106ba-01e7-4745-9646-3907d15b28df"


class MqttStateTests(unittest.TestCase):
    def setUp(self):
        self.service = MqttService()
        self.connection = MagicMock()
        self.device = {
            "device_id": 3,
            "device_code": "P001-IRRIG",
            "device_type": "irrigation",
            "plot_id": 1,
            "status": "online",
            "switch_state": "on",
            "switch_changed_at": None,
        }
        self.service._find_device = MagicMock(return_value=self.device)
        self.service._touch_device = MagicMock(return_value=self.device)
        self.service._update_switch_state = MagicMock()

    def state_payload(self, reason: str) -> dict[str, object]:
        return {
            "seq": 501,
            "ts": 1788264000000,
            "deviceId": IRRIGATION_UUID,
            "switch": "off",
            "reason": reason,
            "values": {},
        }

    def test_local_stop_updates_switch_and_records_successful_close(self):
        transaction = MagicMock()
        transaction.__enter__.return_value = self.connection
        with patch("backend.app.mqtt.engine.begin", return_value=transaction):
            self.service._handle_state(self.state_payload("local"))

        self.service._update_switch_state.assert_called_once()
        self.connection.execute.assert_called_once()
        params = self.connection.execute.call_args.args[1]
        self.assertEqual(params["action_type"], "off")
        self.assertEqual(params["activation_type"], "manual")

    def test_remote_state_updates_switch_without_duplicate_record(self):
        transaction = MagicMock()
        transaction.__enter__.return_value = self.connection
        with patch("backend.app.mqtt.engine.begin", return_value=transaction):
            self.service._handle_state(self.state_payload("remote"))

        self.service._update_switch_state.assert_called_once()
        self.connection.execute.assert_not_called()

    def test_state_uptime_uses_device_timestamp_fallback(self):
        expected = datetime(2026, 9, 3, 12, 0, 0)
        self.service._parse_device_timestamp = MagicMock(return_value=expected)
        payload = self.state_payload("heartbeat")
        payload["ts"] = 664750
        transaction = MagicMock()
        transaction.__enter__.return_value = self.connection

        with patch("backend.app.mqtt.engine.begin", return_value=transaction):
            self.service._handle_state(payload)

        self.service._parse_device_timestamp.assert_called_once()
        self.assertEqual(self.service._touch_device.call_args.args[2], expected)

    def test_heartbeat_uptime_uses_device_timestamp_fallback(self):
        expected = datetime(2026, 9, 3, 12, 0, 0)
        self.service._parse_device_timestamp = MagicMock(return_value=expected)
        transaction = MagicMock()
        transaction.__enter__.return_value = self.connection
        payload = {
            "seq": 502,
            "ts": 664750,
            "type": "snapshot",
            "sensors": [
                {
                    "deviceId": IRRIGATION_UUID,
                    "switch": "off",
                    "name": "P001-IRRIG",
                    "values": {},
                }
            ],
        }

        with patch("backend.app.mqtt.engine.begin", return_value=transaction):
            self.service._handle_heartbeat(payload)

        self.service._parse_device_timestamp.assert_called_once()
        self.assertEqual(self.service._touch_device.call_args.args[2], expected)


if __name__ == "__main__":
    unittest.main()
