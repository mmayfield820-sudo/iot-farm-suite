# Smart Farm Backend
# FastAPI 业务服务：鉴权、MQTT 订阅、RAG 反代
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（利用 Docker 层缓存，改代码不用重装依赖）
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制后端源码
COPY backend/ ./backend/

EXPOSE 8080

# 启动 FastAPI。--reload 本地调试用，生产不加
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
