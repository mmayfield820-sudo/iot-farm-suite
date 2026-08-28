"""告警业务服务。"""

from sqlalchemy.engine import Engine

from src.modules.alert.repository import AlertRepository


class AlertService:
    """编排告警和告警规则查询用例。"""

    def __init__(self, repository: AlertRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: Engine) -> "AlertService":
        return cls(AlertRepository(engine))

    def list_alerts(self) -> list[dict]:
        return self._repository.list_alerts()

    def list_rules(self) -> list[dict]:
        return self._repository.list_rules()

    def save_rule(self, plot_id: int, threshold: float) -> dict | None:
        return self._repository.save_rule(plot_id, threshold)

    def acknowledge_alert(self, alert_id: int) -> dict | None:
        return self._repository.acknowledge_alert(alert_id)