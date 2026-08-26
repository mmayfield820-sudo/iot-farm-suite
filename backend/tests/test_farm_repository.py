"""农场数据访问层测试。"""

import unittest
from unittest.mock import MagicMock

from src.modules.farm.repository import FarmRepository


class FarmRepositoryTest(unittest.TestCase):
    """验证 farms 查询结果可以转换为 API 字段。"""

    def test_list_farms_formats_public_ids(self) -> None:
        engine = MagicMock()
        connection = engine.connect.return_value.__enter__.return_value
        connection.execute.return_value.mappings.return_value.all.return_value = [
            {"farm_id": 1, "farm_name": "绿野示范农场"},
        ]

        result = FarmRepository(engine).list_farms()

        self.assertEqual(result, [{"id": "F001", "name": "绿野示范农场"}])