"""遥测 API 路由。"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.database.connection import get_engine
from src.modules.telemetry.schemas import MetricPointResponse
from src.modules.telemetry.service import TelemetryService


router = APIRouter(prefix="/plots", tags=["Telemetry"])


@router.get("/{plotId}/metrics", response_model=list[MetricPointResponse])
def list_plot_metrics(
    plotId: str,
    metric_type: str = Query(..., alias="type"),
    start: datetime = Query(..., alias="from"),
    end: datetime = Query(..., alias="to"),
) -> list[dict]:
    """查询指定地块时间范围内的温度或湿度。"""
    if not plotId.startswith("P") or not plotId[1:].isdigit():
        raise HTTPException(status_code=400, detail="plotId 格式应为 P001")
    if metric_type not in {"temperature", "humidity"}:
        raise HTTPException(
            status_code=422, detail="type 只能是 temperature 或 humidity"
        )
    if start > end:
        raise HTTPException(status_code=400, detail="from 不能晚于 to")

    return TelemetryService.from_engine(get_engine()).list_metrics(
        int(plotId[1:]), metric_type, start, end
    )