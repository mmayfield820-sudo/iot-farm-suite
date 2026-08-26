"""农场 API 的请求和响应模型。"""

from pydantic import BaseModel, ConfigDict


class FarmResponse(BaseModel):
    """与 contracts/openapi.yaml 中 Farm 对齐的响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str