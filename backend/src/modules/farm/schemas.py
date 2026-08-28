"""农场 API 的请求和响应模型。"""

from pydantic import BaseModel, ConfigDict


class FarmResponse(BaseModel):
    """与 contracts/openapi.yaml 中 Farm 对齐的响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class PlotResponse(BaseModel):
    """农场总览中的地块信息。"""

    id: str
    farmId: str
    name: str


class MetricPointResponse(BaseModel):
    """农场总览中的指标点。"""

    type: str
    value: float
    unit: str
    ts: str


class DeviceResponse(BaseModel):
    """农场总览中的设备信息。"""

    id: str
    deviceNo: str
    type: str
    plotId: str
    status: str
    lastSeenAt: str | None = None


class PlotOverviewResponse(BaseModel):
    """与 contracts/openapi.yaml 中 PlotOverview 对齐的响应。"""

    plot: PlotResponse
    latestMetrics: list[MetricPointResponse]
    devices: list[DeviceResponse]