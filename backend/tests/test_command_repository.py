"""灌溉指令数据访问层测试。"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.modules.command.repository import CommandRepository


class CommandRepositoryTest(unittest.TestCase):
    """验证灌溉指令字段映射。"""

    def test_get_command_formats_record(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        result = MagicMock()
        result.mappings.return_value.first.return_value = {
            "record_id": 1,
            "device_id": 3,
            "action_type": "ON",
            "status": "SUCCESS",
            "requested_at": datetime(2026, 8, 24, 9, 31),
            "executed_at": datetime(2026, 8, 24, 9, 31, 3),
        }
        connection.execute.return_value = result

        command = CommandRepository(engine).get_command(1)

        self.assertEqual(command["commandId"], "CMD0001")
        self.assertEqual(command["deviceId"], "D003")
        self.assertEqual(command["action"], "irrigation_on")
        self.assertEqual(command["status"], "success")