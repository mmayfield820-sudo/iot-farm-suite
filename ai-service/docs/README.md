# 农业灌溉 RAG 服务说明

## 配置

服务按顺序读取仓库根目录 `.env` 和 `ai-service/.env`，后者可覆盖前者。最小配置：

```dotenv
AI_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL_API_KEY=replace-with-your-api-key
AI_MODEL_NAME=qwen3.8-27b
AI_MODEL_TIMEOUT_SECONDS=120
AI_MODEL_ENABLE_THINKING=false
```

不要把真实 API Key 写进源码、示例文件或 Git。`ai-service/.env.example` 提供了完整变量清单。

## 启动

```powershell
cd ai-service
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe app.py
```

主后端使用仓库根目录的 `AI_SERVICE_URL`（默认 `http://localhost:8000`）调用该服务。云模型响应可能超过 10 秒，主后端默认等待 120 秒，也可用 `AI_SERVICE_TIMEOUT_SECONDS` 调整。

## 接口

原提交接口：

```http
POST /chat
Content-Type: application/json

{
  "question": "番茄怎么浇水",
  "session_id": "conversation-1",
  "user_id": "U001",
  "plot_id": "P001"
}
```

当前系统兼容接口：

```http
POST /chat/sessions/conversation-1/messages
Content-Type: application/json

{
  "message": "现在需要浇水吗？",
  "userId": "U001",
  "plotId": "P001",
  "context": {
    "plotName": "1号温室",
    "soilMoisture": 62,
    "soilMoistureThreshold": 70
  }
}
```

第二个接口由主后端调用，`context` 是主后端完成用户鉴权后查询的真实地块数据。响应中的 `sources` 可直接供前端展示。

## 检索模式

仓库没有提交生成物 `vector_db/chroma`。服务因此具备两种模式：

- `local`：默认从 `农业知识来源/农业知识库.md` 做本地文本检索，无需 embedding API。
- `chroma`：运行 `python build_vector_db.py` 后自动启用向量检索。

向量服务使用以下可选变量；未配置时复用 `AI_MODEL_BASE_URL` 和 `AI_MODEL_API_KEY`：

```dotenv
AI_EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_EMBEDDING_API_KEY=replace-with-your-api-key
AI_EMBEDDING_MODEL=text-embedding-v3
```

更换 embedding 模型后必须重建向量库，否则新查询向量与已有数据不在同一向量空间。

## 可选联网搜索

设置 `BOCHA_API_KEY` 后，涉及最新信息或知识库不足的首轮问题会调用博查搜索；未配置时会向模型明确提供“联网搜索未配置”的信息，不影响普通知识库问答。

## 数据与隐私

用户档案和长期记忆分别写入 `user_profile_{user_id}.json` 与 `user_memories_{user_id}.json`。这些文件以及 `.env`、向量库均已在 `ai-service/.gitignore` 中排除。
