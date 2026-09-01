"""MQTT 离线和指令超时巡检测试。"""

from datetime import datetime
import unittest
from unittest.mock import MagicMock

from src.mqtt.health_monitor import MqttHealthMonitor


class MqttHealthMonitorTest(unittest.TestCase):
    def test_run_once_marks_offline_devices_and_timed_out_commands(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        offline_result = MagicMock()
        offline_result.mappings.return_value.all.return_value = [{"device_id": 1, "plot_id": 1}]
        timeout_result = MagicMock()
        timeout_result.mappings.return_value.all.return_value = [{"record_id": 9, "device_id": 3, "plot_id": 1}]
        connection.execute.side_effect = [
            offline_result, MagicMock(), MagicMock(), timeout_result,
            MagicMock(), MagicMock(),
        ]
        monitor = MqttHealthMonitor(engine, 120, 30, 10)

        result = monitor.run_once(datetime(2026, 8, 31, 12, 0, 0))

        self.assertEqual(result, {"offlineDevices": 1, "timedOutCommands": 1})
        self.assertEqual(connection.execute.call_count, 6)


if __name__ == "__main__":
    unittest.main()
