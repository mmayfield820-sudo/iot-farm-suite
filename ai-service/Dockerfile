# Smart Farm AI Service (RAG)
# 农业知识库 + 联网搜索 + 大模型问答。由后端反代调用，不直接对公网。
# 注意：ai-service 目录名带连字符不是合法包名，代码用相对导入（from .knowledge），
#       所以 WORKDIR 必须落在 ai-service/ 内，以 app.main 启动。
FROM python:3.11-slim

WORKDIR /app

COPY ai-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 源码（app 包）+ 知识库（knowledge.py 用 parents[1]/knowledge-base 定位）
COPY ai-service/app/ ./app/
COPY ai-service/knowledge-base/ ./knowledge-base/

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
