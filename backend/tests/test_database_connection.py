"""需要真实 MySQL 实例的数据库连接集成测试。"""

#用下列命令运行测试：
"""
$env:PYTHONPATH="$PWD\backend"
python -m unittest discover -s backend\tests -p "test_*.py" -v
"""


import unittest

from sqlalchemy import text

from src.database.connection import get_engine


class DatabaseConnectionTest(unittest.TestCase):
    """验证后端可以访问已初始化的 smart_agriculture 数据库。"""

    def test_show_tables(self) -> None:
        """执行 SHOW TABLES，并将实际结果输出到终端。"""
        with get_engine().connect() as connection:
            table_names = sorted(
                connection.execute(text("SHOW TABLES")).scalars().all()
            )

        print("SHOW TABLES:")
        for table_name in table_names:
            print(f"- {table_name}")


if __name__ == "__main__":
    unittest.main()
