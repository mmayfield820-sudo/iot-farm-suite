"""灌溉指令 API 响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class CommandResponse(BaseModel):
    """与 contracts/openapi.yaml 中 Command 对齐的响应。"""

    commandId: str
    deviceId: str
    action: str
    status: str
    createdAt: datetime
    finishedAt: datetime | None = None


class CommandCreateRequest(BaseModel):
    """灌溉指令创建请求。"""

    action: str