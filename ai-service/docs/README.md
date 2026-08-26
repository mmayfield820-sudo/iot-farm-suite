# 农业灌溉 RAG 智能体 —— 启动与使用说明

> 这个服务的作用：接收一个灌溉问题，从《设施蔬菜水肥一体化栽培技术》这本书里检索相关知识点，再让大模型基于这些知识点回答。

## 这个目录里有什么

`rag/` 文件夹的目录结构，每个文件是干嘛的写在旁边：

```text
C3/rag/
├── app.py                        # 服务本体：知识库检索 + 联网搜索 + 多轮对话 + 用户记忆
├── web_search.py                 # 博查联网搜索工具（Key 已填）
├── custom_embeddings.py          # embedding 封装（地基，别换）
├── build_vector_db.py            # 建向量库：切块 → embedding → 存 Chroma
├── retrieve.py                   # 检索演示 + 效果评估
├── view_vector_db.py             # 查看向量库内容
├── test_chat.py                  # 调试问答脚本（支持 --sid / --uid）
├── requirements.txt              # 依赖清单
├── user_profile_{user_id}.json   # 长期用户档案（对话后自动生成，每用户一份）
├── user_memories_{user_id}.json  # 长期记忆（对话后自动生成，每用户一份）
├── __pycache__/                  # Python 字节码缓存（自动生成，可删，不用管）
├── vector_db/
│   └── chroma/                   # Chroma 向量库（别删，除非重建）
├── 农业知识来源/                  # 知识库源文件：farming book.txt（书正文）+ OCR 脚本
└── docs/
    └── README.md                 # 本文件：启动 / 测试 / 排障
```

> 📌 **`user_profile_{user_id}.json` 和 `user_memories_{user_id}.json` 在 app.py 同级目录**（即 `C3/rag/` 下）。
> 它们是用户和 `/chat` 聊上话（非闲聊）后**自动生成**的，现在目录里没有属正常——没跑过对话就没有。
> 删除某个用户的文件 = 该用户"失忆"。
> 📌 **`__pycache__/` 是 Python 运行时的字节码缓存**，自动生成、可随时删、不用管，建议加进 `.gitignore`。

知识库源文件：`农业知识来源/farming book.txt`（书正文，向量库的数据来源）

> ⚠️ 关于 embedding：教程默认的 `langchain_openai.OpenAIEmbeddings` 在硅基流动上会算出**不一致**的向量（同一个句子余弦相似度只有 0.248，检索全乱）。所以这里用 `custom_embeddings.py` 包了一层原生 openai client，向量和 app.py 基线版完全一致（余弦 0.9999）。重建向量库用 `build_vector_db.py` 即可。

## 一、怎么启动

打开终端，切到本目录，运行：

```bash
cd C3/rag
python app.py
```

- **前置**：大模型走本地 **Ollama**（`qwen2.5:7b`，已安装）。确保 Ollama 服务在跑（`ollama serve`，或桌面应用 `ollama app.exe`），且模型已拉取（`ollama pull qwen2.5:7b`）。Ollama 已设开机自启，通常不用手动开。
- 启动时直接加载已建好的向量库（`vector_db/chroma`），**秒开**
- 看到下面这行就说明启动成功了：

```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> ⚠️ 这个终端窗口**别关**，关掉服务就停了。
> 💡 想换成云端 DeepSeek-V3：改 [app.py](C3/rag/app.py) 顶部三行配置（Ollama 那组注释掉，恢复硅基流动那组），见 app.py 里注释。

## 二、访问网址

| 网址                           | 作用                      |
| ---------------------------- | ----------------------- |
| `http://localhost:8000/`     | 健康检查，看服务活没活着            |
| `http://localhost:8000/docs` | 自动生成的 API 调试页面          |
| `http://localhost:8000/chat` | 真正的问答接口（POST，给后端 B 调用的） |

**`/chat` 请求体**（支持多轮对话）：

```json
{
  "question": "番茄怎么浇水",
  "session_id": "user-123",     // 可选。同一个 session_id 算同一段对话，会记住上下文
  "user_id": "zhang-001",       // 可选。用户唯一标识，档案/记忆按它隔离，务必传真实用户 id
  "token": "<JWT>",             // 可选。后端传当前用户 token，RAG 拿它调后端取实时农场数据
  "plot_id": "P001"             // 可选。用户当前选的地块，决定查哪块地的实时数据
}
```

## 二点五、联网搜索（已配置完成）

知识库没收录、或问题要"最新/价格/行情"这类实时信息时，服务会自动调**博查（Bocha）**联网搜索。

**当前状态**：✅ 已配置完成 —— `web_search.py` 里 `BOCHA_API_KEY` 已填，且在 open.bochaai.com 控制台**领取了免费资源包**（仅填 Key 不领取会报 403 `not enough money or package quota`）。实测返回真实网页数据（如广州日报蔬菜价格监测）。

**如果 Key 失效 / 换账号，重新配置：**

1. 打开 <https://open.bochaai.com> 注册登录
2. 控制台创建 API Key，**并领取免费资源包**（关键步骤）
3. 打开 `web_search.py`，把 Key 粘到 `BOCHA_API_KEY`
4. 重启服务生效

> 不填 Key 也能跑：联网时返回"未配置"提示，大模型会用通用常识兜底。每次默认返回 5 条结果（`count=5`）。

## 二点六、长期用户档案（自动记忆，可选看）

系统会自动**记住用户**：每轮对话后，用一次调用从"用户说的话"里抽取种植档案（作物/设施/规模/地区/偏好），
写到 `user_profile_{user_id}.json`，下一轮开始注入提示词。效果：换个会话、甚至重启服务，助手都记得
"这个用户种番茄、日光温室、偏好有机肥"，回答更贴合。

- **按 `user_id` 隔离**：每个用户一份文件，互不共享（不同用户的记忆不会污染彼此）
- 查看：直接打开 `user_profile_{user_id}.json`（如 `user_profile_zhang-001.json`）
- 想"失忆"重来：删除对应的 `user_profile_{user_id}.json` 即可
- 寒暄闲聊不触发抽取（省调用）；档案里没有的信息模型不会乱猜

## 二点七、长期记忆（提取式、去重，可选看）

在用户档案之上，系统还会把对话里**值得记住的用户情况**（比如"用户计划今年 3 月定植番茄""用户想扩大种植规模"）抽取出来，
写到 `user_memories_{user_id}.json`，同样每轮注入提示词。和档案的区别：

|     | 用户档案 `user_profile_{user_id}.json` | 长期记忆 `user_memories_{user_id}.json` |
| --- | ---------------------------------- | ----------------------------------- |
| 记什么 | 稳定的基本情况（作物/设施/规模/偏好）               | 具体的计划、安排、临时偏好等事件                    |
| 条数  | 固定几个字段                             | 最多 30 条短句，近似去重                      |

- 寒暄闲聊不抽取；用户只是**问**某个作物不算他种这个作物，不会被记进档案
- 想"失忆"重来：删除对应的 `user_profile_{user_id}.json` 和 `user_memories_{user_id}.json` 即可
- **2026-08-24 已改为按 `user_id` 隔离**：每个用户独立一份档案和记忆，不再全局共享

## 二点八、实时农场数据（对接后端 B，当前为 stub）

问"现在湿度多少"这类**要查实时数据**的问题时，服务会调队友后端的 `GET /farms/{farmId}/overview`
拿实时农场数据，注入给大模型再回答（refs 里会出现 `实时农场数据(后端)`）。

- **当前状态**：`app.py` 里 `ENABLE_FARM_API=False` → 不真调网络，返回**假数据**把链路跑通（实测
  "现在大棚湿度多少"能答出"1号温室湿度 40.5%"）。后端接口就绪后把开关改成 `True` 即可，逻辑不用动。
- **判断方式**：独立的一次便宜 LLM 判断（`needs_realtime()`）——只判断"要不要实时数据"，不掺进四态判断器。
  实测：现在湿度→要实时、番茄怎么浇水→不要、今天番茄价格→不要、你好→不要。
- **token / plot_id**：请求体里 `token` 是后端传入的用户 JWT（方式 A，RAG 拿它调后端接口鉴权）；
  `plot_id` 是用户当前选的地块。都不传也能跑（只是取不到带鉴权的实时数据 / 查整场概况）。

## 三、怎么测试（三选一）

**① 最简单 —— 用调试脚本：**

```bash
python test_chat.py
```

进入交互模式，输入问题回车，输入 `q` 退出。也可以直接带问题跑：

```bash
python test_chat.py 黄瓜结瓜盛期怎么浇水
```

> 🧠 **支持多轮对话**：交互模式里连续问，它会记住之前聊的内容，能回答"那什么时候浇水？"这种指代问题。想另开一段对话，加 `--sid 名字`；想换用户测记忆隔离，加 `--uid 用户id`。

```bash
python test_chat.py --sid 会话A          # 开一段新对话（独立的上下文）
python test_chat.py --uid user_a 种番茄   # 以 user_a 身份提问（档案/记忆按它隔离）
```

**② 浏览器 —— 打开 `/docs` 页面：**

1. 浏览器打开 `http://localhost:8000/docs`
2. 点开 `POST /chat` 那一行
3. 点右上角 `Try it out`
4. 在 `question` 后面填问题，点 `Execute`
5. 往下翻能看到返回的 `answer` 和 `refs`

**③ 命令行 curl**（注意 Windows 上中文会乱码，不推荐，用 ① 或 ②）：

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"question\":\"hello\"}"
```

## 四、怎么关

在跑服务的那个终端里按 **`Ctrl+C`**。

## 五、教程进度与向量库

服务是**教程版 + 联网升级 + 用户记忆**。处理逻辑：

```
用户问题
  → ① 每轮确定性检索 Chroma 知识库（top3，不靠模型自觉 → 稳定）
  → ② 判断要不要联网（四态）：
       时效性问题（最新/今天/价格/行情/20xx年）→ 必须联网
       其他 → 用一次便宜的模型评估：闲聊 / 足够 / 部分 / 不足
       · 足够 → 直接基于知识库答
       · 部分 → 资料为骨架 + 农业常识推断（标注（推断）），不联网
       · 不足 → 联网搜索
       · 闲聊 → 纯聊天，不检索不联网
       （额外：要不要实时农场数据，由独立的 needs_realtime() 单独判一次，不掺进四态）
  → ③ 把【私有知识库资料】或【联网搜索结果】注入给大模型（注入用户档案+长期记忆；
      需要实时数据时再注入【实时农场数据】，来自后端 overview，开发期是假数据）
  → ④ 大模型用自己的话组织答案，末尾带【文献参考】小字来源
  → ⑤ 非闲聊时抽取更新该用户的档案 + 长期记忆（按 user_id 隔离）
```

**多轮对话**（教程 4.2.5 的概念）：同一 `session_id` 的问题会记住，下一轮"那…呢"能接上。记忆存在内存里（`session_store` 字典），重启即清空。

> ⚠️ **为什么不用 langchain 的 agent 工具调用（create_agent）来触发联网？**
> 实测 DeepSeek-V3 在硅基流动上工具调用不稳定：有时口头答应"我去搜索"却不真调用，有时直接把工具调用语法当正文输出（乱码）。演示不可控。
> 所以改成**确定性编排**：搜索由代码直接调博查 API 触发，模型只负责"基于资料好好回答"。联网依然是"搜索引擎 API"这层工程，只是触发不再赌模型自觉。
> 
> ⚠️ 为什么不用教程原版的 `RetrievalQA` / `ConversationBufferMemory`：langchain 1.3 已把它们移除。app.py 里用手写等价链路实现，概念完全一致。

- 建库：`python build_vector_db.py`（已建好 489 块，chunk 500/重叠 100，重跑会覆盖重建）
- 检索演示 / 评估：`python retrieve.py`（或 `python retrieve.py 一个问题` 对比三种检索方式）
- 查看库里内容：`python view_vector_db.py`

用 Chroma 检索的写法（教程里的 `Chroma(persist_directory=..., embedding_function=...)`）：

```python
from langchain_chroma import Chroma
from custom_embeddings import SiliconFlowEmbeddings

vectordb = Chroma(
    persist_directory="vector_db/chroma",
    collection_name="farming_book",
    embedding_function=SiliconFlowEmbeddings(),
)
res = vectordb.similarity_search("黄瓜结瓜盛期怎么浇水", k=3)
```

## 六、常见问题

| 现象                              | 原因                             | 解决                                                                 |
| ------------------------------- | ------------------------------ | ------------------------------------------------------------------ |
| `address already in use` / 端口被占 | 已经有一个服务在跑，占了 8000 端口（通常是旧终端没关） | 找到旧终端按 Ctrl+C 关掉；想临时换端口：`uvicorn app:app --port 8001`              |
| 回答报连接 11434 失败 / Ollama 连不上     | Ollama 服务没在跑                   | 运行 `ollama serve`，或打开 `ollama app.exe` 桌面应用                        |
| 提示模型不存在                         | 没 `ollama pull` 那个模型           | `ollama pull qwen2.5:7b`                                           |
| 回答质量明显变差                        | 本地 7B 比云端 DeepSeek-V3 弱        | 可切回云端：改 `app.py` 顶部三行配置                                            |
| 联网一直 403 / 报 quota              | 博查 Key 有效但账号没领免费资源包或没充值        | 去 open.bochaai.com 控制台**领取免费资源包**（见「二点五」）                          |
| 想换知识库内容 / 重新切块                  | 向量库里还是旧数据                      | 删掉 `vector_db/chroma` 文件夹，重跑 `python build_vector_db.py`           |
| 前端网页连不上接口                       | CORS / 局域网访问问题                 | 服务要用 `uvicorn app:app --host 0.0.0.0 --port 8000` 启动并放行防火墙 8000 端口 |

## 六、别忘了

- 当前大模型走本地 **Ollama**，不需要 API Key；`app.py` 里残留的硅基流动 key 属于历史配置，**也别提交到 Git / 别发给别人**。
- **embedding 别换**：向量库用 `bge-m3` 建的，换 embedding 会导致检索全乱。
