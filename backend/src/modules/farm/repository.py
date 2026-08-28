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

    def get_overview(self, farm_id: int) -> list[dict]:
        """查询农场下的地块、设备和最新指标。"""
        plot_statement = text(
            "SELECT plot_id, farm_id, plot_name "
            "FROM plots "
            "WHERE farm_id = :farm_id "
            "ORDER BY plot_id"
        )
        device_statement = text(
            "SELECT device_id, device_code, mqtt_device_id, device_type, plot_id, status, "
            "last_heartbeat "
            "FROM devices "
            "WHERE plot_id = :plot_id "
            "ORDER BY device_id"
        )
        with self._engine.connect() as connection:
            plots = connection.execute(
                plot_statement, {"farm_id": farm_id}
            ).mappings().all()

            overview = []
            for plot in plots:
                devices = connection.execute(
                    device_statement, {"plot_id": plot["plot_id"]}
                ).mappings().all()
                overview.append(
                    {
                        "plot": {
                            "id": f"P{plot['plot_id']:03d}",
                            "farmId": f"F{plot['farm_id']:03d}",
                            "name": plot["plot_name"],
                        },
                        "latestMetrics": [],
                        "devices": [
                            self._to_device_response(device)
                            for device in devices
                        ],
                    }
                )

        return overview

    @staticmethod
    def _to_device_response(row: dict) -> dict:
        """将数据库设备枚举转换为 API 契约枚举。"""
        device_types = {
            "TEMPERATURE_SENSOR": "temperature",
            "SOIL_MOISTURE_SENSOR": "humidity",
            "IRRIGATION_CONTROLLER": "irrigation",
        }
        statuses = {"ONLINE": "online", "OFFLINE": "offline"}
        last_seen_at = row["last_heartbeat"]
        return {
            "id": f"D{row['device_id']:03d}",
            "deviceNo": row["device_code"],
            "mqttDeviceId": row["mqtt_device_id"],
            "type": device_types[row["device_type"]],
            "plotId": f"P{row['plot_id']:03d}",
            "status": statuses[row["status"]],
            "lastSeenAt": (
                last_seen_at.isoformat() if last_seen_at is not None else None
            ),
        }