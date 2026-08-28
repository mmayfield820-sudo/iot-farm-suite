"""遥测 API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class MetricPointResponse(BaseModel):
    """与 contracts/openapi.yaml 中 MetricPoint 对齐的响应。"""

    type: str
    value: float
    unit: str
    ts: datetime