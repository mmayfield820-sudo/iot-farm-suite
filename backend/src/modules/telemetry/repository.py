"""遥测数据访问逻辑。"""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


class TelemetryRepository:
    """负责从 MQTT 原始遥测表读取历史指标。"""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_metrics(
        self,
        plot_id: int,
        metric_type: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        """按地块、指标类型和时间范围查询历史指标。"""
        statement = text(
            "SELECT t.metric_type, t.metric_value, t.reported_at "
            "FROM device_telemetry t "
            "JOIN devices d ON d.device_id = t.device_id "
            "WHERE d.plot_id = :plot_id "
            "AND t.metric_type = :metric_type "
            "AND t.reported_at >= :start AND t.reported_at <= :end "
            "ORDER BY t.reported_at"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                statement,
                {"plot_id": plot_id, "metric_type": metric_type, "start": start, "end": end},
            ).mappings().all()

        return [
            {
                "type": row["metric_type"],
                "value": float(row["metric_value"]),
                "unit": "%" if row["metric_type"] == "humidity" else "C",
                "ts": row["reported_at"],
            }
            for row in rows
        ]
