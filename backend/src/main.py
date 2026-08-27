"""后端应用入口。"""

from fastapi import FastAPI

from src.modules.farm.router import router as farm_router


app = FastAPI(title="Smart Farm API", version="0.1.0")
app.include_router(farm_router, prefix="/api")