"""告警 API 路由。"""

from fastapi import APIRouter, HTTPException

from src.database.connection import get_engine
from src.modules.alert.schemas import (
    AlertResponse,
    AlertRuleRequest,
    AlertRuleResponse,
)
from src.modules.alert.service import AlertService


router = APIRouter(tags=["Alerts"])


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts() -> list[dict]:
    """查询全部告警记录。"""
    return AlertService.from_engine(get_engine()).list_alerts()


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
def list_alert_rules() -> list[dict]:
    """查询现有告警规则。"""
    return AlertService.from_engine(get_engine()).list_rules()


@router.post("/alert-rules", response_model=AlertRuleResponse)
def save_alert_rule(request: AlertRuleRequest) -> dict:
    """创建或更新一个地块的土壤湿度告警规则。"""
    if not request.plotId.startswith("P") or not request.plotId[1:].isdigit():
        raise HTTPException(status_code=400, detail="plotId 格式应为 P001")
    if request.metricType != "humidity" or request.operator != "<":
        raise HTTPException(
            status_code=422,
            detail="当前数据库仅支持 humidity 指标的小于阈值规则",
        )
    if not 0 <= request.threshold <= 100:
        raise HTTPException(status_code=422, detail="threshold 范围应为 0 到 100")

    result = AlertService.from_engine(get_engine()).save_rule(
        int(request.plotId[1:]), request.threshold
    )
    if result is None:
        raise HTTPException(status_code=404, detail="地块不存在")
    return result


@router.post("/alerts/{alertId}/ack", response_model=AlertResponse)
def acknowledge_alert(alertId: str) -> dict:
    """确认指定告警。"""
    if not alertId.startswith("A") or not alertId[1:].isdigit():
        raise HTTPException(status_code=400, detail="alertId 格式应为 A0001")

    result = AlertService.from_engine(get_engine()).acknowledge_alert(
        int(alertId[1:])
    )
    if result is None:
        raise HTTPException(status_code=404, detail="告警不存在")
    return result