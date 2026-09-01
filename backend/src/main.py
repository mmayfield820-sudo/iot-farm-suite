"""后端应用入口。"""

from fastapi import FastAPI

from src.modules.auth.router import router as auth_router
from src.modules.alert.router import router as alert_router
from src.modules.command.router import (
	device_command_router,
	router as command_router,
)
from src.modules.device.router import router as device_router
from src.modules.farm.router import router as farm_router
from src.modules.telemetry.router import router as telemetry_router
from src.mqtt.client import create_mqtt_client
from src.mqtt.health_monitor import MqttHealthMonitor
from src.config.settings import get_mqtt_settings
from src.database.connection import get_engine


app = FastAPI(title="Smart Farm API", version="0.1.0")
app.state.mqtt_client = None
app.state.mqtt_health_monitor = None


@app.get("/")
def root() -> dict[str, str]:
    """项目入口，避免访问根路径时返回 404。"""
    return {"message": "Smart Farm API", "docs": "/docs"}


@app.on_event("startup")
def startup() -> None:
    """启动时初始化 MQTT 客户端，以便后端接收传感器和指令消息。"""
    app.state.mqtt_client = create_mqtt_client()
    app.state.mqtt_client.connect()
    settings = get_mqtt_settings()
    app.state.mqtt_health_monitor = MqttHealthMonitor(
        get_engine(),
        offline_after_seconds=settings.device_offline_seconds,
        command_timeout_seconds=settings.command_timeout_seconds,
        interval_seconds=settings.monitor_interval_seconds,
    )
    app.state.mqtt_health_monitor.start()


@app.on_event("shutdown")
def shutdown() -> None:
    """关闭时断开 MQTT 连接，避免资源泄漏。"""
    mqtt_client = app.state.mqtt_client
    monitor = app.state.mqtt_health_monitor
    if monitor is not None:
        monitor.stop()
    if mqtt_client is not None:
        mqtt_client.disconnect()


app.include_router(auth_router, prefix="/api")
app.include_router(alert_router, prefix="/api")
app.include_router(command_router, prefix="/api")
app.include_router(device_command_router, prefix="/api")
app.include_router(device_router, prefix="/api")
app.include_router(farm_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
