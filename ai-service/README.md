# AI 服务（RAG 智能体）

该目录基于提交 `316e45c` 的农业知识库、RAG 编排、联网搜索、多轮对话与长期记忆实现，并兼容当前智慧农场前端/主后端接口。

模型通过 OpenAI 兼容环境变量配置。真实密钥只放在仓库根目录 `.env` 或 `ai-service/.env`，不要提交到 Git。

```powershell
cd ai-service
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe app.py
```

服务默认监听 `http://127.0.0.1:8000`：

- `GET /health`：模型与检索状态
- `POST /chat`：原提交接口
- `POST /chat/sessions/{session_id}/messages`：当前主后端兼容接口
- `GET /docs`：OpenAPI 调试页面

未构建 `vector_db/chroma` 时，服务会使用随仓库提供的本地农业知识文本检索；需要向量检索时运行 `python build_vector_db.py`。详细配置见 [docs/README.md](docs/README.md)。
