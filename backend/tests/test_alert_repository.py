"""告警数据访问层测试。"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.modules.alert.repository import AlertRepository


class AlertRepositoryTest(unittest.TestCase):
    """验证告警和规则字段映射。"""

    def test_list_alerts_maps_status_and_metric(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.all.return_value = [
            {
                "alert_id": 1,
                "plot_id": 2,
                "alert_type": "LOW_MOISTURE",
                "alert_value": 24.8,
                "alert_threshold": 40.0,
                "alert_datetime": datetime(2026, 8, 24, 9, 30),
                "alert_status": "UNHANDLED",
            },
        ]
        connection.execute.return_value = result

        alert = AlertRepository(engine).list_alerts()[0]

        self.assertEqual(alert["id"], "A0001")
        self.assertEqual(alert["metricType"], "humidity")
        self.assertEqual(alert["status"], "active")

    def test_list_rules_maps_moisture_threshold(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.all.return_value = [
            {"config_id": 1, "plot_id": 1, "soil_moisture_threshold": 35.0},
        ]
        connection.execute.return_value = result

        rule = AlertRepository(engine).list_rules()[0]

        self.assertEqual(rule["plotId"], "P001")
        self.assertEqual(rule["operator"], "<")
        self.assertEqual(rule["threshold"], 35.0)