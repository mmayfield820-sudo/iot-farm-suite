"""设备数据访问逻辑。"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


class DeviceRepository:
    """负责读取 devices 表。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_devices(self, plot_id: int | None = None) -> list[dict]:
        """查询全部设备，或查询指定地块下的设备。"""
        statement = text(
            "SELECT device_id, device_code, mqtt_device_id, device_type, plot_id, status, "
            "last_heartbeat "
            "FROM devices "
            "WHERE (:plot_id IS NULL OR plot_id = :plot_id) "
            "ORDER BY device_id"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                statement, {"plot_id": plot_id}
            ).mappings().all()
        return [self._to_device_response(row) for row in rows]

    def get_status(self, device_id: int) -> dict | None:
        """按设备 ID 查询设备状态。"""
        statement = text(
            "SELECT device_id, status, last_heartbeat "
            "FROM devices "
            "WHERE device_id = :device_id"
        )
        with self._engine.connect() as connection:
            row = connection.execute(
                statement, {"device_id": device_id}
            ).mappings().first()
        if row is None:
            return None

        return {
            "deviceId": f"D{row['device_id']:03d}",
            "status": self._status_name(row["status"]),
            "lastSeenAt": (
                row["last_heartbeat"].isoformat()
                if row["last_heartbeat"] is not None
                else None
            ),
        }

    def create_device(
        self,
        device_code: str,
        mqtt_device_id: str,
        device_type: str,
        plot_id: int,
    ) -> dict:
        """注册设备并绑定到地块。"""
        device_types = {
            "temperature": "TEMPERATURE_SENSOR",
            "humidity": "SOIL_MOISTURE_SENSOR",
            "irrigation": "IRRIGATION_CONTROLLER",
        }
        statement = text(
            "INSERT INTO devices "
            "(device_code, mqtt_device_id, device_type, plot_id) "
            "VALUES (:device_code, :mqtt_device_id, :device_type, :plot_id)"
        )
        with self._engine.begin() as connection:
            result = connection.execute(
                statement,
                {
                    "device_code": device_code,
                    "mqtt_device_id": mqtt_device_id,
                    "device_type": device_types[device_type],
                    "plot_id": plot_id,
                },
            )
            device_id = result.lastrowid
        return self.get_device(device_id)

    def bind_device(self, device_id: int, plot_id: int) -> dict | None:
        """将设备绑定到指定地块。"""
        plot_statement = text(
            "SELECT plot_id FROM plots WHERE plot_id = :plot_id"
        )
        update_statement = text(
            "UPDATE devices SET plot_id = :plot_id "
            "WHERE device_id = :device_id"
        )
        with self._engine.begin() as connection:
            plot = connection.execute(
                plot_statement, {"plot_id": plot_id}
            ).first()
            if plot is None:
                raise ValueError("plot_not_found")
            result = connection.execute(
                update_statement,
                {"device_id": device_id, "plot_id": plot_id},
            )
            if result.rowcount == 0:
                return None
        return self.get_device(device_id)

    def unbind_device(self, device_id: int) -> bool:
        """解除设备与地块的绑定。"""
        statement = text(
            "UPDATE devices SET plot_id = NULL "
            "WHERE device_id = :device_id"
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement, {"device_id": device_id})
        return result.rowcount > 0

    def get_device(self, device_id: int) -> dict | None:
        """按主键查询设备完整信息。"""
        statement = text(
            "SELECT device_id, device_code, mqtt_device_id, device_type, "
            "plot_id, status, last_heartbeat FROM devices "
            "WHERE device_id = :device_id"
        )
        with self._engine.connect() as connection:
            row = connection.execute(
                statement, {"device_id": device_id}
            ).mappings().first()
        return self._to_device_response(row) if row is not None else None

    @classmethod
    def _to_device_response(cls, row: dict) -> dict:
        """将数据库设备字段转换为 API 字段。"""
        device_types = {
            "TEMPERATURE_SENSOR": "temperature",
            "SOIL_MOISTURE_SENSOR": "humidity",
            "IRRIGATION_CONTROLLER": "irrigation",
        }
        return {
            "id": f"D{row['device_id']:03d}",
            "deviceNo": row["device_code"],
            "mqttDeviceId": row["mqtt_device_id"],
            "type": device_types[row["device_type"]],
            "plotId": (
                f"P{row['plot_id']:03d}"
                if row["plot_id"] is not None
                else None
            ),
            "status": cls._status_name(row["status"]),
            "lastSeenAt": (
                row["last_heartbeat"].isoformat()
                if row["last_heartbeat"] is not None
                else None
            ),
        }

    @staticmethod
    def _status_name(status: str) -> str:
        return {"ONLINE": "online", "OFFLINE": "offline"}[status]