"""设备数据访问层测试。"""

import unittest
from unittest.mock import MagicMock

from src.modules.device.repository import DeviceRepository


class DeviceRepositoryTest(unittest.TestCase):
    """验证设备数据和状态枚举映射。"""

    def test_list_devices_formats_device_data(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.all.return_value = [
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
        connection.execute.return_value = result

        devices = DeviceRepository(engine).list_devices()

        self.assertEqual(devices[0]["id"], "D001")
        self.assertEqual(devices[0]["type"], "humidity")
        self.assertEqual(devices[0]["status"], "online")
        self.assertEqual(devices[0]["mqttDeviceId"], "device_001")

    def test_get_status_formats_status_data(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.first.return_value = {
            "device_id": 1,
            "status": "OFFLINE",
            "last_heartbeat": None,
        }
        connection.execute.return_value = result

        status = DeviceRepository(engine).get_status(1)

        self.assertEqual(status, {
            "deviceId": "D001",
            "status": "offline",
            "lastSeenAt": None,
        })