"""设备 API 的响应模型。"""

from pydantic import BaseModel


class DeviceResponse(BaseModel):
    """与 contracts/openapi.yaml 中 Device 对齐的设备响应。"""

    id: str
    deviceNo: str
    mqttDeviceId: str | None = None
    type: str
    plotId: str | None = None
    status: str
    lastSeenAt: str | None = None


class DeviceStatusResponse(BaseModel):
    """设备在线状态响应。"""

    deviceId: str
    status: str
    lastSeenAt: str | None = None


class DeviceCreateRequest(BaseModel):
    """注册设备请求。"""

    deviceNo: str
    mqttDeviceId: str
    type: str
    plotId: str


class DeviceBindRequest(BaseModel):
    """设备绑定请求。"""

    plotId: str