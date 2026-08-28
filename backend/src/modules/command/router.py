"""灌溉指令 API 路由。"""

from fastapi import APIRouter, HTTPException

from src.database.connection import get_engine
from src.modules.command.schemas import CommandCreateRequest, CommandResponse
from src.modules.command.service import CommandService


router = APIRouter(prefix="/commands", tags=["Commands"])
device_command_router = APIRouter(tags=["Commands"])


@router.get("/{commandId}", response_model=CommandResponse)
def get_command(commandId: str) -> dict:
    """查询指定灌溉指令的执行状态。"""
    if not commandId.startswith("CMD") or not commandId[3:].isdigit():
        raise HTTPException(
            status_code=400, detail="commandId 格式应为 CMD0001"
        )

    result = CommandService.from_engine(get_engine()).get_command(
        int(commandId[3:])
    )
    if result is None:
        raise HTTPException(status_code=404, detail="指令不存在")
    return result


@device_command_router.post(
    "/devices/{deviceId}/commands",
    response_model=CommandResponse,
    status_code=202,
)
def create_command(
    deviceId: str, request: CommandCreateRequest
) -> dict:
    """创建灌溉指令并记录为待执行状态。"""
    if not deviceId.startswith("D") or not deviceId[1:].isdigit():
        raise HTTPException(status_code=400, detail="deviceId 格式应为 D001")
    if request.action not in {"irrigation_on", "irrigation_off"}:
        raise HTTPException(status_code=422, detail="不支持的灌溉操作")

    result = CommandService.from_engine(get_engine()).create_command(
        int(deviceId[1:]), request.action
    )
    if result is None:
        raise HTTPException(status_code=404, detail="设备不存在或不是灌溉控制器")
    return result