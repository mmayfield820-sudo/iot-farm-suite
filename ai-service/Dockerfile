# Smart Farm AI Service (RAG)
# 农业知识库 + 联网搜索 + 大模型问答。由后端反代调用，不直接对公网。
FROM python:3.11-slim

WORKDIR /app

COPY ai-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 新版服务入口是 ai-service/app.py；同时复制检索器与随仓库交付的知识库。
COPY ai-service/ ./

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
