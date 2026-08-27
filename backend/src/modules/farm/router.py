"""农场 API 路由。"""

from fastapi import APIRouter

from src.database.connection import get_engine
from src.modules.farm.schemas import FarmResponse
from src.modules.farm.service import FarmService


router = APIRouter(prefix="/farms", tags=["Farms"])


@router.get("", response_model=list[FarmResponse])
def list_farms() -> list[dict[str, str]]:
    """返回数据库中的全部农场。"""
    service = FarmService.from_engine(get_engine())
    return service.list_farms()