"""遥测数据访问逻辑。"""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine


class TelemetryRepository:
    """负责从 plot_reports 表读取历史指标。"""

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
            "SELECT plot_moisture, temperature, report_datetime "
            "FROM plot_reports "
            "WHERE plot_id = :plot_id "
            "AND report_datetime >= :start "
            "AND report_datetime <= :end "
            "ORDER BY report_datetime"
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                statement,
                {"plot_id": plot_id, "start": start, "end": end},
            ).mappings().all()

        if metric_type == "humidity":
            return [
                {
                    "type": "humidity",
                    "value": float(row["plot_moisture"]),
                    "unit": "%",
                    "ts": row["report_datetime"],
                }
                for row in rows
            ]

        return [
            {
                "type": "temperature",
                "value": float(row["temperature"]),
                "unit": "C",
                "ts": row["report_datetime"],
            }
            for row in rows
        ]