"""认证业务服务。"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.engine import Engine

from src.modules.auth.repository import AuthRepository


class AuthService:
    """验证登录凭据并签发 JWT。"""

    def __init__(self, repository: AuthRepository, jwt_secret: str) -> None:
        self._repository = repository
        self._jwt_secret = jwt_secret

    @classmethod
    def from_engine(cls, engine: Engine) -> "AuthService":
        """使用数据库 Engine 创建认证服务。"""
        from src.config.settings import get_jwt_secret

        return cls(AuthRepository(engine), get_jwt_secret())

    def login(self, username: str, password: str) -> dict:
        """验证账号并返回契约规定的登录响应。"""
        user = self._repository.find_user_by_username(username)
        if user is None or user["user_status"] != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        password_matches = bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        )
        if not password_matches:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )

        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user["user_id"]),
            "username": user["username"],
            "role": self._role_name(user["role_code"]),
            "iat": now,
            "exp": now + timedelta(hours=2),
        }
        token = jwt.encode(payload, self._jwt_secret, algorithm="HS256")
        return {
            "token": token,
            "user": {
                "id": f"U{user['user_id']:03d}",
                "username": user["username"],
                "role": self._role_name(user["role_code"]),
            },
        }

    @staticmethod
    def _role_name(role_code: str | None) -> str:
        role_names = {
            "SYSTEM_ADMIN": "system_admin",
            "FARM_MANAGER": "farm_admin",
            "FARMER": "farmer",
            "VIEWER": "farmer",
        }
        return role_names.get(role_code, "farmer")