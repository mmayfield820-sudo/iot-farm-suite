"""农场业务服务。"""

from sqlalchemy.engine import Engine

from src.modules.farm.repository import FarmRepository


class FarmService:
    """编排农场查询用例。"""

    def __init__(self, repository: FarmRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: Engine) -> "FarmService":
        """使用数据库 Engine 创建农场服务。"""
        return cls(FarmRepository(engine))

    def list_farms(self) -> list[dict[str, str]]:
        """查询全部农场。"""
        return self._repository.list_farms()