"""农场数据访问逻辑。"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


class FarmRepository:
    """负责从 farms 表读取农场数据。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_farms(self) -> list[dict[str, str]]:
        """查询所有农场，并转换为 API 层需要的字段。"""
        statement = text(
            "SELECT farm_id, farm_name "
            "FROM farms "
            "ORDER BY farm_id"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [
            {"id": f"F{row['farm_id']:03d}", "name": row["farm_name"]}
            for row in rows
        ]