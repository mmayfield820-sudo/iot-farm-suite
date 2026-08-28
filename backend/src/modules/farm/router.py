"""农场 API 路由。"""

from fastapi import APIRouter, HTTPException

from src.database.connection import get_engine
from src.modules.farm.schemas import FarmResponse, PlotOverviewResponse
from src.modules.farm.service import FarmService


router = APIRouter(prefix="/farms", tags=["Farms"])


@router.get("", response_model=list[FarmResponse])
def list_farms() -> list[dict[str, str]]:
    """返回数据库中的全部农场。"""
    service = FarmService.from_engine(get_engine())
    return service.list_farms()


@router.get("/{farm_id}/overview", response_model=list[PlotOverviewResponse])
def get_farm_overview(farm_id: str) -> list[dict]:
    """返回指定农场下所有地块的当前概况。"""
    if not farm_id.startswith("F") or not farm_id[1:].isdigit():
        raise HTTPException(status_code=400, detail="farmId 格式应为 F001")

    service = FarmService.from_engine(get_engine())
    overview = service.get_overview(int(farm_id[1:]))
    if not overview:
        raise HTTPException(status_code=404, detail="农场不存在或没有地块")
    return overview