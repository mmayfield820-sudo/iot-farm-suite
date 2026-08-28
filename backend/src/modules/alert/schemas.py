"""告警 API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    """与 contracts/openapi.yaml 中 Alert 对齐的响应。"""

    id: str
    plotId: str
    metricType: str | None = None
    value: float | None = None
    threshold: float | None = None
    status: str
    triggeredAt: datetime


class AlertRuleResponse(BaseModel):
    """与 contracts/openapi.yaml 中 AlertRule 对齐的响应。"""

    id: str
    plotId: str
    metricType: str
    operator: str
    threshold: float
    enabled: bool


class AlertRuleRequest(BaseModel):
    """创建或更新土壤湿度告警规则的请求。"""

    plotId: str
    metricType: str
    operator: str
    threshold: float
    enabled: bool = True