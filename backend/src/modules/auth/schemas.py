"""认证 API 的请求和响应模型。"""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求。"""

    username: str
    password: str


class UserResponse(BaseModel):
    """登录响应中的用户信息。"""

    id: str
    username: str
    role: str


class LoginResponse(BaseModel):
    """登录成功响应。"""

    token: str
    user: UserResponse