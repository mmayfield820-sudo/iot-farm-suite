# AI 服务（RAG 智能体）

农业知识库 + RAG 检索 + 智能问答接口。被后端调用（`POST /chat`），不直接操作 MQTT 设备。

- 详细启动 / 测试 / 排障 / 接口字段说明：见 [docs/README.md](docs/README.md)

**快速启动：**

```bash
cd ai-service
python app.py        # 默认 8000 端口，浏览器开 http://localhost:8000/docs
```

前置：本地 Ollama（qwen2.5:7b）需在跑。

**机密说明**：API key 放在本地 `local_secrets.py`（已被 `.gitignore` 排除，不入库），
其他人拉取后需自行创建该文件或在环境变量里配置对应 key 才能使用联网 / embedding 功能。
