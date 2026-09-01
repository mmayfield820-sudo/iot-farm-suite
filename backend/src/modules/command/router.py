"""灌溉指令 API 路由。"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

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
    deviceId: str, request: CommandCreateRequest, http_request: Request
) -> dict:
    """创建灌溉指令并记录为待执行状态。"""
    if not deviceId.startswith("D") or not deviceId[1:].isdigit():
        raise HTTPException(status_code=400, detail="deviceId 格式应为 D001")
    if request.action not in {"irrigation_on", "irrigation_off"}:
        raise HTTPException(status_code=422, detail="不支持的灌溉操作")

    service = CommandService.from_engine(get_engine())
    result = service.create_command(
        int(deviceId[1:]), request.action
    )
    if result is None:
        raise HTTPException(status_code=404, detail="设备不存在或不是灌溉控制器")
    record_id = int(result["commandId"][3:])
    mqtt_device_id = service.get_mqtt_device_id(record_id)
    mqtt_client = http_request.app.state.mqtt_client
    try:
        if mqtt_client is None or mqtt_device_id is None:
            raise RuntimeError("MQTT 客户端或设备通信标识不可用")
        mqtt_client.publish(
            f"farm/command/{mqtt_device_id}",
            {
                "commandId": result["commandId"],
                "deviceId": mqtt_device_id,
                "action": request.action,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )
    except RuntimeError as error:
        service.mark_publish_failed(record_id)
        raise HTTPException(status_code=503, detail="MQTT 服务暂不可用，指令未下发") from error
    return result
