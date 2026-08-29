# AI 服务使用与维护说明

## 1. 当前结构

```text
ai-service/
├── app/
│   ├── main.py       # FastAPI 接口、会话和模型调用
│   ├── knowledge.py  # 本地农业知识库检索
│   └── search.py     # 博查联网搜索及触发规则
├── knowledge-base/   # 当前运行时读取的知识库
├── requirements.txt
└── README.md
```

旧版根目录 `app.py` 已移除，不再维护第二套接口。

## 2. 环境变量

环境变量统一放在项目根目录 `.env`：

| 变量 | 必需 | 作用 |
|---|---:|---|
| `AI_MODEL_BASE_URL` | 是 | OpenAI 兼容模型地址，当前为本地 Ollama |
| `AI_MODEL_API_KEY` | 是 | Ollama 可使用占位值 `ollama` |
| `AI_MODEL_NAME` | 是 | 当前模型名称 |
| `AI_MODEL_TIMEOUT_SECONDS` | 否 | AI 服务等待模型回答的秒数 |
| `BOCHA_API_KEY` | 联网时是 | 博查搜索密钥；留空时关闭联网搜索 |
| `BOCHA_TIMEOUT_SECONDS` | 否 | 搜索请求超时，默认 20 秒 |
| `AI_LOCAL_TIMEZONE` | 否 | 展开“今天/明天”所用时区，默认 `Asia/Shanghai` |

不要把真实 API Key 提交到 Git。

## 3. 接口

### 健康检查

```http
GET /health
```

示例：

```json
{
  "status": "ok",
  "knowledgeDocuments": 4,
  "modelEnabled": true,
  "searchEnabled": false
}
```

`searchEnabled=false` 表示没有配置博查密钥，不影响普通知识库问答。

### 发送问题

```http
POST /chat/sessions/{sessionId}/messages
Content-Type: application/json
```

请求示例：

```json
{
  "message": "今天东区温室会下雨吗？",
  "plotId": "P001",
  "userId": "U002",
  "context": {
    "plotName": "一号田地",
    "location": "东区温室",
    "soilMoisture": 36,
    "soilMoistureThreshold": 35
  }
}
```

响应示例：

```json
{
  "sessionId": "WEB123",
  "answer": "……",
  "sources": [
    "知识库：灌溉决策",
    "https://example.com/weather"
  ]
}
```

正常业务中由 8080 后端补充经过权限检查的地块上下文，前端不应直接向 8000 发送敏感业务数据。

## 4. 联网与降级流程

```text
用户问题
  → 本地知识库检索
  → 判断是否包含时效关键词
      → 否：地块数据 + 知识库 → Ollama
      → 是：调用博查搜索
          → 成功：地块数据 + 知识库 + 搜索结果/网址/查询时间 → Ollama
          → 失败：地块数据 + 知识库 → Ollama，并追加降级说明
```

网页内容只作为外部资料，不作为系统指令。灌溉开关仍必须由用户在业务页面二次确认。

## 5. 配置联网搜索

1. 在博查开放平台创建 API Key，并确认账号有可用额度。
2. 将 Key 写入根目录 `.env` 的 `BOCHA_API_KEY`。
3. 重启 AI 服务。
4. 访问 `http://127.0.0.1:8000/health`，确认 `searchEnabled` 为 `true`。
5. 用包含“今天”或“最新”的问题测试，检查响应 `sources` 是否包含网页地址。

## 6. 常见问题

- `searchEnabled=false`：没有设置 `BOCHA_API_KEY`，或 AI 服务尚未重启。
- 回答带“联网搜索暂不可用”：查看密钥、额度、网络和 `BOCHA_TIMEOUT_SECONDS`。
- 普通灌溉问题没有搜索：这是预期行为；只有时效问题才调用搜索。
- 回答较慢：本地 7B 模型通常需要数十秒，前端智能体请求已单独设置较长超时。
