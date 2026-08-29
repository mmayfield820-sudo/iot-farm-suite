# AI 服务

当前 AI 服务以 `app/main.py` 为唯一入口，提供农业知识库检索、地块上下文问答、Ollama 模型调用和可选的博查联网搜索。

## 启动

在项目根目录完成 `.env` 配置后运行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir ai-service
```

也可以使用项目根目录的 `start-all.cmd` 一键启动全部服务。

## 联网搜索

在根目录 `.env` 中填写：

```dotenv
BOCHA_API_KEY=你的博查API密钥
BOCHA_TIMEOUT_SECONDS=20
```

包含“今天、明天、最新、天气、降雨、价格、行情、新闻”等时效关键词的问题会触发搜索。没有配置密钥、搜索超时或服务报错时，问答会继续执行，并明确说明本次回答已降级为仅使用农田数据和本地知识库。

详细接口、数据流和排障说明见 [docs/README.md](docs/README.md)。
