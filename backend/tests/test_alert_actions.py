"""告警写入操作测试。"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.modules.alert.repository import AlertRepository


class AlertActionsRepositoryTest(unittest.TestCase):
    """验证规则保存和告警确认。"""

    def test_save_rule_returns_rule(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        plot_result = MagicMock()
        plot_result.first.return_value = (1,)
        row_result = MagicMock()
        row_result.mappings.return_value.first.return_value = {
            "config_id": 1,
            "plot_id": 1,
            "soil_moisture_threshold": 35.0,
        }
        connection.execute.side_effect = [plot_result, MagicMock(), row_result]

        rule = AlertRepository(engine).save_rule(1, 35.0)

        self.assertEqual(rule["id"], "R0001")
        self.assertEqual(rule["threshold"], 35.0)

    def test_acknowledge_alert_returns_acknowledged_alert(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        row_result = MagicMock()
        row_result.mappings.return_value.first.return_value = {
            "alert_id": 1,
            "plot_id": 2,
            "alert_type": "LOW_MOISTURE",
            "alert_value": 24.8,
            "alert_threshold": 40.0,
            "alert_datetime": datetime(2026, 8, 24, 9, 30),
            "alert_status": "HANDLING",
        }
        connection.execute.side_effect = [MagicMock(), row_result]

        alert = AlertRepository(engine).acknowledge_alert(1)

        self.assertEqual(alert["id"], "A0001")
        self.assertEqual(alert["status"], "acknowledged")