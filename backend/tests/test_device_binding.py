"""设备绑定和解绑数据访问层测试。"""

import unittest
from unittest.mock import MagicMock

from src.modules.device.repository import DeviceRepository


class DeviceBindingRepositoryTest(unittest.TestCase):
    """验证设备绑定和解绑操作。"""

    def test_bind_device_rejects_missing_plot(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        connection.execute.return_value.first.return_value = None

        with self.assertRaisesRegex(ValueError, "plot_not_found"):
            DeviceRepository(engine).bind_device(1, 99)

    def test_unbind_device_returns_update_result(self) -> None:
        engine = MagicMock()
        connection = engine.begin.return_value.__enter__.return_value
        connection.execute.return_value.rowcount = 1

        self.assertTrue(DeviceRepository(engine).unbind_device(1))