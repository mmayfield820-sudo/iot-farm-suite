"""从环境变量读取后端运行配置。"""

from dataclasses import dataclass
import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class DatabaseSettings:
    """MySQL 数据库连接配置。"""

    host: str
    port: int
    user: str
    password: str
    name: str


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少数据库配置: {name}")
    return value


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """读取并缓存数据库配置。"""
    port = int(os.getenv("DB_PORT", "3306"))
    return DatabaseSettings(
        host=_required_env("DB_HOST"),
        port=port,
        user=_required_env("DB_USER"),
        password=_required_env("DB_PASSWORD"),
        name=os.getenv("DB_NAME", "smart_agriculture"),
    )


@lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """读取 JWT 签名密钥。"""
    return _required_env("JWT_SECRET")