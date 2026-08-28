"""农场总览数据访问层测试。"""

import unittest
from unittest.mock import MagicMock

from src.modules.farm.repository import FarmRepository


class FarmOverviewRepositoryTest(unittest.TestCase):
    """验证农场总览的地块和设备映射。"""

    def test_get_overview_formats_plot_and_device_data(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        plot_result = MagicMock()
        plot_result.mappings.return_value.all.return_value = [
            {"plot_id": 1, "farm_id": 1, "plot_name": "一号温室"},
        ]
        device_result = MagicMock()
        device_result.mappings.return_value.all.return_value = [
            {
                "device_id": 1,
                "device_code": "GH01-SOIL-001",
                "mqtt_device_id": "device_001",
                "device_type": "SOIL_MOISTURE_SENSOR",
                "plot_id": 1,
                "status": "ONLINE",
                "last_heartbeat": None,
            },
        ]
        connection.execute.side_effect = [plot_result, device_result]

        result = FarmRepository(engine).get_overview(1)

        self.assertEqual(result[0]["plot"]["id"], "P001")
        self.assertEqual(result[0]["devices"][0]["type"], "humidity")
        self.assertEqual(result[0]["devices"][0]["status"], "online")