"""遥测数据访问层测试。"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.modules.telemetry.repository import TelemetryRepository


class TelemetryRepositoryTest(unittest.TestCase):
    """验证温度和湿度指标映射。"""

    def test_list_metrics_formats_humidity(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.all.return_value = [
            {
                "metric_type": "humidity",
                "metric_value": 42.5,
                "reported_at": datetime(2026, 8, 24, 9),
            },
        ]
        connection.execute.return_value = result

        metrics = TelemetryRepository(engine).list_metrics(
            1, "humidity", datetime(2026, 8, 24), datetime(2026, 8, 25)
        )

        self.assertEqual(metrics[0]["value"], 42.5)
        self.assertEqual(metrics[0]["unit"], "%")
        self.assertEqual(metrics[0]["type"], "humidity")
