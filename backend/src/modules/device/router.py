"""设备 API 路由。"""

from fastapi import APIRouter, HTTPException, Query, Response

from src.database.connection import get_engine
from src.modules.device.schemas import (
    DeviceBindRequest,
    DeviceCreateRequest,
    DeviceResponse,
    DeviceStatusResponse,
)
from src.modules.device.service import DeviceService


router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    plot_id: str | None = Query(default=None, alias="plotId"),
) -> list[dict]:
    """查询全部设备，或查询指定地块的设备。"""
    database_plot_id = None
    if plot_id is not None:
        if not plot_id.startswith("P") or not plot_id[1:].isdigit():
            raise HTTPException(
                status_code=400, detail="plotId 格式应为 P001"
            )
        database_plot_id = int(plot_id[1:])

    return DeviceService.from_engine(get_engine()).list_devices(
        database_plot_id
    )


@router.post("", response_model=DeviceResponse, status_code=201)
def create_device(request: DeviceCreateRequest) -> dict:
    """注册并绑定设备。"""
    if request.type not in {"temperature", "humidity", "irrigation"}:
        raise HTTPException(status_code=422, detail="不支持的设备类型")
    if not request.plotId.startswith("P") or not request.plotId[1:].isdigit():
        raise HTTPException(status_code=400, detail="plotId 格式应为 P001")
    return DeviceService.from_engine(get_engine()).create_device(
        request.deviceNo,
        request.mqttDeviceId,
        request.type,
        int(request.plotId[1:]),
    )


@router.post("/{deviceId}/bind", response_model=DeviceResponse)
def bind_device(deviceId: str, request: DeviceBindRequest) -> dict:
    """将设备绑定到指定地块。"""
    if not deviceId.startswith("D") or not deviceId[1:].isdigit():
        raise HTTPException(status_code=400, detail="deviceId 格式应为 D001")
    if not request.plotId.startswith("P") or not request.plotId[1:].isdigit():
        raise HTTPException(status_code=400, detail="plotId 格式应为 P001")

    try:
        result = DeviceService.from_engine(get_engine()).bind_device(
            int(deviceId[1:]), int(request.plotId[1:])
        )
    except ValueError as error:
        if str(error) == "plot_not_found":
            raise HTTPException(status_code=404, detail="地块不存在") from error
        raise
    if result is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return result


@router.delete("/{deviceId}/bind", status_code=204)
def unbind_device(deviceId: str) -> Response:
    """解除设备与地块的绑定。"""
    if not deviceId.startswith("D") or not deviceId[1:].isdigit():
        raise HTTPException(status_code=400, detail="deviceId 格式应为 D001")

    unbound = DeviceService.from_engine(get_engine()).unbind_device(
        int(deviceId[1:])
    )
    if not unbound:
        raise HTTPException(status_code=404, detail="设备不存在")
    return Response(status_code=204)


@router.get("/{deviceId}/status", response_model=DeviceStatusResponse)
def get_device_status(deviceId: str) -> dict:
    """查询指定设备的在线状态。"""
    if not deviceId.startswith("D") or not deviceId[1:].isdigit():
        raise HTTPException(status_code=400, detail="deviceId 格式应为 D001")

    result = DeviceService.from_engine(get_engine()).get_status(
        int(deviceId[1:])
    )
    if result is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return result