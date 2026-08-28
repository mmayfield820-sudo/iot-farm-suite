"""灌溉指令数据访问逻辑。"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


class CommandRepository:
    """负责读取 irrigation_records 表。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_command(self, record_id: int) -> dict | None:
        """按数据库记录 ID 查询灌溉指令。"""
        statement = text(
            "SELECT record_id, device_id, action_type, status, requested_at, "
            "executed_at "
            "FROM irrigation_records "
            "WHERE record_id = :record_id"
        )
        with self._engine.connect() as connection:
            row = connection.execute(
                statement, {"record_id": record_id}
            ).mappings().first()
        if row is None:
            return None

        actions = {"ON": "irrigation_on", "OFF": "irrigation_off"}
        statuses = {
            "PENDING": "pending",
            "SUCCESS": "success",
            "FAILED": "failed",
            "TIMEOUT": "timeout",
        }
        return {
            "commandId": f"CMD{row['record_id']:04d}",
            "deviceId": f"D{row['device_id']:03d}",
            "action": actions[row["action_type"]],
            "status": statuses[row["status"]],
            "createdAt": row["requested_at"],
            "finishedAt": row["executed_at"],
        }

    def create_command(
        self, device_id: int, action: str, operator_id: int | None = None
    ) -> dict | None:
        """为灌溉控制器创建待执行指令。"""
        actions = {"irrigation_on": "ON", "irrigation_off": "OFF"}
        statement = text(
            "INSERT INTO irrigation_records "
            "(plot_id, device_id, action_type, activation_type, operator_id) "
            "SELECT plot_id, device_id, :action_type, 'MANUAL', :operator_id "
            "FROM devices "
            "WHERE device_id = :device_id "
            "AND device_type = 'IRRIGATION_CONTROLLER'"
        )
        with self._engine.begin() as connection:
            result = connection.execute(
                statement,
                {
                    "device_id": device_id,
                    "action_type": actions[action],
                    "operator_id": operator_id,
                },
            )
            if result.rowcount == 0:
                return None
            record_id = result.lastrowid
        return self.get_command(record_id)