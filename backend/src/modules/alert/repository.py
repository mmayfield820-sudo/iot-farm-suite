"""告警数据访问逻辑。"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


class AlertRepository:
    """负责读取 alerts 和 threshold_configs 表。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_alerts(self) -> list[dict]:
        """查询全部告警并转换为 API 字段。"""
        statement = text(
            "SELECT alert_id, plot_id, alert_type, alert_value, "
            "alert_threshold, alert_datetime, alert_status "
            "FROM alerts ORDER BY alert_datetime DESC, alert_id DESC"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        alert_types = {"LOW_MOISTURE": "humidity"}
        statuses = {
            "UNHANDLED": "active",
            "HANDLING": "acknowledged",
            "HANDLED": "recovered",
        }
        return [
            {
                "id": f"A{row['alert_id']:04d}",
                "plotId": f"P{row['plot_id']:03d}",
                "metricType": alert_types.get(row["alert_type"]),
                "value": (
                    float(row["alert_value"])
                    if row["alert_value"] is not None
                    else None
                ),
                "threshold": (
                    float(row["alert_threshold"])
                    if row["alert_threshold"] is not None
                    else None
                ),
                "status": statuses[row["alert_status"]],
                "triggeredAt": row["alert_datetime"],
            }
            for row in rows
        ]

    def list_rules(self) -> list[dict]:
        """查询现有地块土壤湿度阈值配置。"""
        statement = text(
            "SELECT config_id, plot_id, soil_moisture_threshold "
            "FROM threshold_configs ORDER BY config_id"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()

        return [
            {
                "id": f"R{row['config_id']:04d}",
                "plotId": f"P{row['plot_id']:03d}",
                "metricType": "humidity",
                "operator": "<",
                "threshold": float(row["soil_moisture_threshold"]),
                "enabled": True,
            }
            for row in rows
        ]

    def save_rule(
        self, plot_id: int, threshold: float, updated_by: int | None = None
    ) -> dict | None:
        """新增或更新一个地块的土壤湿度阈值。"""
        plot_statement = text(
            "SELECT plot_id FROM plots WHERE plot_id = :plot_id"
        )
        upsert_statement = text(
            "INSERT INTO threshold_configs "
            "(plot_id, soil_moisture_threshold, updated_by) "
            "VALUES (:plot_id, :threshold, :updated_by) "
            "ON DUPLICATE KEY UPDATE "
            "soil_moisture_threshold = VALUES(soil_moisture_threshold), "
            "updated_by = VALUES(updated_by)"
        )
        select_statement = text(
            "SELECT config_id, plot_id, soil_moisture_threshold "
            "FROM threshold_configs WHERE plot_id = :plot_id"
        )
        with self._engine.begin() as connection:
            if connection.execute(
                plot_statement, {"plot_id": plot_id}
            ).first() is None:
                return None
            connection.execute(
                upsert_statement,
                {
                    "plot_id": plot_id,
                    "threshold": threshold,
                    "updated_by": updated_by,
                },
            )
            row = connection.execute(
                select_statement, {"plot_id": plot_id}
            ).mappings().first()
        if row is None:
            return None
        return {
            "id": f"R{row['config_id']:04d}",
            "plotId": f"P{row['plot_id']:03d}",
            "metricType": "humidity",
            "operator": "<",
            "threshold": float(row["soil_moisture_threshold"]),
            "enabled": True,
        }

    def acknowledge_alert(self, alert_id: int) -> dict | None:
        """将未处理告警标记为处理中。"""
        update_statement = text(
            "UPDATE alerts SET alert_status = 'HANDLING' "
            "WHERE alert_id = :alert_id AND alert_status = 'UNHANDLED'"
        )
        select_statement = text(
            "SELECT alert_id, plot_id, alert_type, alert_value, "
            "alert_threshold, alert_datetime, alert_status "
            "FROM alerts WHERE alert_id = :alert_id"
        )
        with self._engine.begin() as connection:
            connection.execute(update_statement, {"alert_id": alert_id})
            row = connection.execute(
                select_statement, {"alert_id": alert_id}
            ).mappings().first()
        if row is None:
            return None

        alert_types = {"LOW_MOISTURE": "humidity"}
        statuses = {
            "UNHANDLED": "active",
            "HANDLING": "acknowledged",
            "HANDLED": "recovered",
        }
        return {
            "id": f"A{row['alert_id']:04d}",
            "plotId": f"P{row['plot_id']:03d}",
            "metricType": alert_types.get(row["alert_type"]),
            "value": (
                float(row["alert_value"])
                if row["alert_value"] is not None
                else None
            ),
            "threshold": (
                float(row["alert_threshold"])
                if row["alert_threshold"] is not None
                else None
            ),
            "status": statuses[row["alert_status"]],
            "triggeredAt": row["alert_datetime"],
        }