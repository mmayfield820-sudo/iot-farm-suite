"""认证 API 路由。"""

from fastapi import APIRouter

from src.database.connection import get_engine
from src.modules.auth.schemas import LoginRequest, LoginResponse
from src.modules.auth.service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> dict:
    """处理用户名和密码登录。"""
    return AuthService.from_engine(get_engine()).login(
        request.username, request.password
    )