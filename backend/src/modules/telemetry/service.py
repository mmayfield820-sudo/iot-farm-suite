"""遥测业务服务。"""

from datetime import datetime

from sqlalchemy.engine import Engine

from src.modules.telemetry.repository import TelemetryRepository


class TelemetryService:
    """编排历史指标查询用例。"""

    def __init__(self, repository: TelemetryRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: Engine) -> "TelemetryService":
        return cls(TelemetryRepository(engine))

    def list_metrics(
        self,
        plot_id: int,
        metric_type: str,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        return self._repository.list_metrics(
            plot_id, metric_type, start, end
        )