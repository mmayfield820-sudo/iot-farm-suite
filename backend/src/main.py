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


app = FastAPI(title="Smart Farm API", version="0.1.0")
app.include_router(auth_router, prefix="/api")
app.include_router(alert_router, prefix="/api")
app.include_router(command_router, prefix="/api")
app.include_router(device_command_router, prefix="/api")
app.include_router(device_router, prefix="/api")
app.include_router(farm_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")