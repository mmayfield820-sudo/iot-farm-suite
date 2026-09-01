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

    def get_mqtt_device_id(self, record_id: int) -> str | None:
        """取得待下发指令对应的 MQTT 通信标识。"""
        statement = text(
            "SELECT d.mqtt_device_id FROM irrigation_records r "
            "JOIN devices d ON d.device_id = r.device_id "
            "WHERE r.record_id = :record_id AND r.status = 'PENDING'"
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement, {"record_id": record_id}).mappings().first()
        return row["mqtt_device_id"] if row is not None else None

    def mark_publish_failed(self, record_id: int) -> None:
        """Broker 不可用或发布失败时结束指令，避免永久停留在 pending。"""
        statement = text(
            "UPDATE irrigation_records SET status = 'FAILED', executed_at = CURRENT_TIMESTAMP "
            "WHERE record_id = :record_id AND status = 'PENDING'"
        )
        with self._engine.begin() as connection:
            connection.execute(statement, {"record_id": record_id})
