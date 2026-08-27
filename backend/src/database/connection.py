"""SQLAlchemy 到 MySQL 的连接边界。"""

from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import URL

from src.config.settings import DatabaseSettings, get_database_settings


def _build_database_url(settings: DatabaseSettings) -> URL:
    """使用结构化 URL，避免密码中的特殊字符破坏连接字符串。"""
    return URL.create(
        drivername="mysql+pymysql",
        username=settings.user,
        password=settings.password,
        host=settings.host,
        port=settings.port,
        database=settings.name,
        query={"charset": "utf8mb4"},
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """创建并缓存 SQLAlchemy Engine。首次调用时不会主动连接数据库。"""
    settings = get_database_settings()
    return create_engine(
        _build_database_url(settings),
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """取得统一的数据库 Session 工厂。"""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_session() -> Iterator[Session]:
    """提供一个带自动关闭的 Session，供应用框架依赖注入使用。"""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> bool:
    """执行一次轻量查询，成功返回 True，失败时保留原始异常。"""
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
