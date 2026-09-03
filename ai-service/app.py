from __future__ import annotations

# -*- coding: utf-8 -*-
"""
农业灌溉 RAG 智能体（基于 316e45c，确定性编排版：知识库检索 + 联网搜索）

数据流：
  用户问题
    → ① 每轮确定性检索 Chroma 私有知识库（不靠模型自觉，保证演示稳定）
    → ② 判断要不要联网：
         - 时效性问题（"最新/今天/价格/行情/20xx年"等）→ 必须联网
         - 其他问题 → 用一次便宜的 LLM 评估"资料够不够"，不够就联网
    → ③ 把【私有知识库资料】和/或【联网搜索结果】注入给大模型
    → ④ 大模型用自己的话组织最终回答，末尾带【文献参考】
  多轮对话：同一 session_id 的问答会被记住，下一轮"那…呢"能接上。

启动：python app.py
测试：python test_chat.py  或浏览器开 http://localhost:8000/docs
接口：POST /chat  {"question": "...", "session_id": "对话编号(可选)"}

模型通过 AI_MODEL_* 环境变量接入任意 OpenAI 兼容服务。搜索由代码确定性触发，
模型只负责分类、记忆提取和基于资料组织回答。
"""
import difflib
import json
import logging
import os
import re
import sys
import requests
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from custom_embeddings import SiliconFlowEmbeddings
from local_retriever import LocalKnowledgeRetriever
from web_search import search_web

# Windows 控制台默认 GBK，打印中文/emoji 会崩，统一转 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SERVICE_DIR = Path(__file__).resolve().parent
load_dotenv(SERVICE_DIR.parent / ".env")
load_dotenv(SERVICE_DIR / ".env", override=True)
logger = logging.getLogger(__name__)

# ===== ① 配置 =====
API_KEY = os.getenv("AI_MODEL_API_KEY", "")
BASE_URL = os.getenv("AI_MODEL_BASE_URL", "").rstrip("/")
LLM_MODEL = os.getenv("AI_MODEL_NAME", "")
MODEL_ENABLED = bool(API_KEY and BASE_URL and LLM_MODEL)

TOP_K = 3             # 知识库每次检索取最相似的几块

VECTOR_DIR = SERVICE_DIR / "vector_db" / "chroma"             # Chroma 向量库位置
COLLECTION = "farming_book"                                    # 库的名字

# ===== ①.5 对接后端 B：实时农场数据（方式 A：token 由后端传入）=====
# 状态：开发期默认关闭（不真调网络，用假数据跑通链路）；后端接口就绪后改 ENABLE_FARM_API=True 并填对地址。
FARM_API_BASE = os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/") + "/api"
FARM_FARM_ID = os.getenv("AI_FARM_ID", "F001")
ENABLE_FARM_API = os.getenv("AI_ENABLE_FARM_API", "false").lower() == "true"

# ===== ② 加载知识库 =====
def load_retriever():
    if (VECTOR_DIR / "chroma.sqlite3").exists():
        try:
            return Chroma(
                persist_directory=str(VECTOR_DIR),
                collection_name=COLLECTION,
                embedding_function=SiliconFlowEmbeddings(),
            ), "chroma"
        except Exception as error:
            logger.warning("Chroma unavailable, using local knowledge fallback: %s", error)
    source = SERVICE_DIR / "农业知识来源" / "农业知识库.md"
    return LocalKnowledgeRetriever(source), "local"


retriever, RETRIEVAL_MODE = load_retriever()

# ===== ③ 大模型 =====
model_options: dict[str, Any] = {}
if "dashscope.aliyuncs.com" in BASE_URL:
    model_options["extra_body"] = {
        "enable_thinking": os.getenv("AI_MODEL_ENABLE_THINKING", "false").lower() == "true"
    }

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=API_KEY or "not-configured",
    base_url=BASE_URL or "http://127.0.0.1:1/v1",
    temperature=0.3,
    timeout=float(os.getenv("AI_MODEL_TIMEOUT_SECONDS", "120")),
    max_retries=2,
    **model_options,
)

# ===== ④ 系统提示词 =====
SYSTEM_PROMPT = """你是一位专业、可靠的设施蔬菜水肥一体化农技助手。
回答风格：客观、理性、有耐心、有亲和力；专业但不晦涩，平实清楚，不用方言土话，不过度热情。
注意：不要介绍或吹嘘自己的身份、资历（不要自称"老农技员""干了多少年"），也不要假设用户是没经验的老农户——
用户可能是刚毕业的大学生、返乡创业者或种植新手，请用平等、尊重、鼓励的语气交流。

每轮对话会提供【私有知识库资料】（来自《设施蔬菜水肥一体化栽培技术》）和/或【联网搜索结果】（博查实时搜索）作为回答依据。

回答规则：
1. 优先依据提供的资料作答：用你自己的话组织成完整、可操作的答案，条理清晰，不逐字照搬原文。
2. 若资料与问题无关或未收录，如实说明"知识库未收录这一信息"，不要硬套、不要编造。
3. 若提供了【联网搜索结果】，以其中的实时信息为准补充回答。
4. 末尾：如果回答中的关键信息来自知识库或联网资料，用一行小字【文献参考】列出来源。
5. 组织方式灵活，不固定步骤。寒暄等与农业无关的话题，简单友好回应即可，不展开。
6. 系统会附带【用户档案】和【长期记忆】：档案是用户的固定情况（作物/设施/偏好），
   长期记忆是之前对话里记住的他的计划、安排等细节。回答时可结合这些背景让建议更贴合，
   但必须**以用户当前问题为第一优先级**：它们只是背景参考，绝不能覆盖或忽略当前问题。
   背景里没有的信息，不要假设、不要编造。
7. 格式：用纯文本加换行分段即可。不要使用 Markdown 加粗标记（也就是别用星号星号把文字括起来），
   可以用"-"或"1."列表，但别用星号包裹文字。"""

# ===== ④.5 长期用户档案（自动抽取，持久化到 user_profile_{user_id}.json）=====
# 作用：跨会话、跨重启记住这个用户种什么、什么设施、什么偏好，
#       每轮注入系统提示词，让回答贴合他的情况。
# 每个 user_id 一份文件，互不共享——否则所有用户会污染同一份记忆。
DEFAULT_PROFILE = {"作物": [], "设施": "", "种植规模": "", "地区": "", "偏好关注点": []}


def _safe_name(s: str) -> str:
    """把 user_id 转成安全的文件名（只留字母数字下划线中文）。"""
    return re.sub(r"[^\w一-龥-]", "_", str(s))


def load_profile(user_id: str = "default") -> dict:
    f = Path(__file__).parent / f"user_profile_{_safe_name(user_id)}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_PROFILE)


def save_profile(profile: dict, user_id: str = "default"):
    f = Path(__file__).parent / f"user_profile_{_safe_name(user_id)}.json"
    f.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def format_profile(profile: dict) -> str:
    """把档案拼成一段能注入提示词的中文。"""
    parts = []
    if profile.get("作物"):
        parts.append("作物：" + "、".join(profile["作物"]))
    if profile.get("设施"):
        parts.append("设施：" + profile["设施"])
    if profile.get("种植规模"):
        parts.append("种植规模：" + profile["种植规模"])
    if profile.get("地区"):
        parts.append("地区：" + profile["地区"])
    if profile.get("偏好关注点"):
        parts.append("偏好/关注：" + "、".join(profile["偏好关注点"]))
    if not parts:
        return "【用户档案】暂无（还不知道这个用户的情况，可从对话中逐步了解）"
    return "【用户档案】" + "；".join(parts) + "（仅供背景参考，务必以用户当前问题为第一优先级）"


# ---- 长期记忆（对话记忆，提取式、去重、持久化到 user_memories_{user_id}.json）----
# 档案存"事实"（种什么/什么设施），记忆存"值得记住的事件和计划"（如"用户计划3月种番茄"）。
MAX_MEMORIES = 30                     # 记忆列表上限，超了不再加（避免无限膨胀）


def load_memories(user_id: str = "default") -> list:
    f = Path(__file__).parent / f"user_memories_{_safe_name(user_id)}.json"
    try:
        m = json.loads(f.read_text(encoding="utf-8"))
        return m if isinstance(m, list) else []
    except Exception:
        return []


def save_memories(memories: list, user_id: str = "default"):
    f = Path(__file__).parent / f"user_memories_{_safe_name(user_id)}.json"
    f.write_text(json.dumps(memories, ensure_ascii=False, indent=2), encoding="utf-8")


def format_memories(memories: list) -> str:
    if not memories:
        return "【长期记忆】暂无"
    items = "\n".join(f"- {m}" for m in memories)
    return f"【长期记忆】\n{items}"


def _is_dup(new_item: str, existing: list) -> bool:
    """近似去重：和已有某条记忆相似度超过 0.8 就算重复（防止模型换句话重复存）。"""
    for e in existing:
        if difflib.SequenceMatcher(None, new_item, e).ratio() > 0.8:
            return True
    return False


EXTRACT_SYS = """你是记忆提取器。根据"用户本轮说的话"，做两件事，只输出一个 JSON 对象：
{"profile": {...}, "new_memories": [...]}

1. profile：更新这个用户的农业种植档案。
   字段：作物(数组)、设施(字符串)、种植规模(字符串)、地区(字符串)、偏好关注点(数组)。
   - 只在用户【明确说自己】种植/使用/偏好某物时，才更新对应字段。
   - 用户只是"问某个作物的技术问题"，并不代表他在种该作物，绝对不要因此改"作物"。
   - 用户明确表达的偏好（如"喜欢用有机肥"）必须记入"偏好关注点"。
   - 没提到的字段保留"当前档案"里的原值。
2. new_memories：从用户的话里挑出【值得长期记住、且当前记忆里还没有】的用户个人情况
   （计划、目标、时间安排、偏好、承诺、重要安排等），转成简洁的一句话放进数组。
   - 只存"用户的情况"，不要存"用户问了某问题"这类对话内容本身。
   - 当前记忆里已经有的信息不要重复输出。没有新信息就输出 []。

规则：只依据用户明确说的话，不要编造；寒暄客套、与农业无关的闲聊不提取。
输出示例：{"profile": {"作物": ["番茄"], "设施": "日光温室", "种植规模": "", "地区": "", "偏好关注点": ["偏好有机肥"]}, "new_memories": ["用户计划2026年3月定植番茄"]}"""


def _extract_json(text: str):
    """从模型输出里抠出第一个 JSON 对象（容忍 ```json 围栏和前后废话）。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    return json.loads(text[start:end + 1])


def extract_memory_turn(question: str, profile: dict, memories: list):
    """一次调用：更新档案 + 提取新增记忆。返回 (新档案, 新记忆列表)；出错返回原样。"""
    try:
        resp = llm.invoke([
            SystemMessage(content=EXTRACT_SYS),
            HumanMessage(
                content=f"当前档案：{json.dumps(profile, ensure_ascii=False)}\n"
                        f"当前记忆：{json.dumps(memories, ensure_ascii=False)}\n\n"
                        f"用户本轮说的话：\n{question}"
            ),
        ]).content
        obj = _extract_json(resp)
        if not isinstance(obj, dict):
            return {}, []
        new_profile = obj.get("profile") if isinstance(obj.get("profile"), dict) else {}
        new_mems = [str(m).strip() for m in obj.get("new_memories", []) if str(m).strip()]
        return new_profile, new_mems
    except Exception:
        return {}, []


def merge_profile(old: dict, new: dict) -> dict:
    """新档案合并进旧档案：列表去重拼接，字符串非空才覆盖。"""
    out = dict(old)
    for key in ("作物", "偏好关注点"):
        vals = [str(x).strip() for x in (new.get(key) or []) if str(x).strip()]
        old_vals = [str(x) for x in out.get(key, [])]
        out[key] = list(dict.fromkeys(old_vals + vals))   # 去重保序
    for key in ("设施", "种植规模", "地区"):
        v = str(new.get(key, "") or "").strip()
        if v:
            out[key] = v
    return out


# ===== ⑤ 判断"要不要联网" =====
# 时效关键词：命中即联网（价格/行情/最新这类问题，知识库再全也不能用旧数据答）
TIMELY_KEYWORDS = ["最新", "今天", "今年", "价格", "行情", "天气", "新闻"]


def is_timely_question(question: str) -> bool:
    """命中时效关键词，或出现"20xx年"，就判定需要实时信息。"""
    if any(k in question for k in TIMELY_KEYWORDS):
        return True
    return bool(re.search(r"20\d\d年", question))


# 用一次便宜的评估调用，判断这问题属于哪一类（四态）：
# 闲聊 = 与农业无关（寒暄/打招呼） → 直接聊天，不检索不联网
# 足够 = 知识库资料直接覆盖        → 直接基于资料回答
# 部分 = 资料只部分相关，结合常识推断能给出合理回答 → 基于资料 + 推断，不联网
# 不足 = 资料基本无关              → 联网搜索
JUDGE_SYSTEM = (
    "你是判断器。阅读下面的【资料】和用户输入，只输出一个词：\n"
    "- 闲聊：与农业无关的寒暄、打招呼、客套（如\"你好\"\"谢谢\"\"在吗\"）\n"
    "- 足够：【资料】直接、完整地覆盖了该问题，足以据此回答\n"
    "- 部分：【资料】只部分相关或间接相关，但结合农业常识合理推断后，能给出一个可用的回答\n"
    "- 不足：【资料】与该问题基本无关，无法据此作答，需要联网搜索\n"
    "注意：用户说\"我种了番茄\"\"我喜欢用有机肥\"这类农业相关的陈述/偏好，"
    "不是闲聊，按资料能否回应归为 足够/部分/不足。"
)


def classify_question(question: str, context: str) -> str:
    """返回 '闲聊' / '足够' / '部分' / '不足'。调用出错时保守返回 '足够'（不乱搜）。
    只做一件事（判断类型），本地 7B 更容易稳定；实时数据与否单独用 needs_realtime() 判。"""
    if not context.strip():
        return "不足"
    try:
        verdict = llm.invoke([
            SystemMessage(content=JUDGE_SYSTEM),
            HumanMessage(content=f"【资料】\n{context}\n\n用户问题：{question}"),
        ]).content.strip()
    except Exception:
        return "足够"
    if "闲聊" in verdict and "不足" not in verdict and "部分" not in verdict:
        return "闲聊"
    if "不足" in verdict:
        return "不足"
    if "部分" in verdict:
        return "部分"
    return "足够"


# ===== ⑤.4 是否需要实时农场数据（独立判断，判断归模型、触发归代码）=====
REALTIME_JUDGE_SYSTEM = (
    "你是判断器。判断下面这个农业问题，是否需要查询『当前农场的实时数据』。\n"
    "需要实时数据的情况：问现在的温度、湿度、灌溉状态、设备状态、要不要浇水等"
    "（这些数值随现实变化，知识库给不了当前的数值）。\n"
    "不需要的情况：问种植知识、方法、原理、市场价格行情等通用问题。\n"
    "只输出一个词：『要实时』或『不要实时』。"
)


def needs_realtime(question: str) -> bool:
    """返回是否需要实时农场数据。只输出判断，真正触发由代码做；
    调用出错时保守返回 False（绝不因为联网失败让问答崩掉）。"""
    try:
        verdict = llm.invoke([
            SystemMessage(content=REALTIME_JUDGE_SYSTEM),
            HumanMessage(content=f"用户问题：{question}"),
        ]).content.strip()
    except Exception:
        return False
    return ("要实时" in verdict) and ("不要实时" not in verdict)


# ===== ⑤.5 对接后端 B：实时农场数据（方式 A：token 由后端传入）=====
# 开发期 ENABLE_FARM_API=False：不真调网络，用假数据把链路跑通；
# 后端接口就绪后改成 True 并填对 FARM_API_BASE，RAG 侧逻辑不用改。
_FAKE_FARM_DATA = {
    "plot": {"id": "P001", "farmId": "F001", "name": "1号温室"},
    "latestMetrics": [
        {"type": "temperature", "value": 25.6, "unit": "C", "ts": "2026-08-24T10:00:00"},
        {"type": "humidity", "value": 40.5, "unit": "%", "ts": "2026-08-24T10:00:00"},
    ],
    "devices": [{"id": "D003", "deviceNo": "SENSOR-003", "type": "irrigation", "status": "online"}],
}


def query_farm_db(plot_id: str = "", token: str = "") -> str:
    """调后端 B 的 GET /farms/{farmId}/overview 拿实时农场数据，转成文本返回。
    - 开发期（ENABLE_FARM_API=False）返回假数据，不真调网络，链路先跑通。
    - 真调时：请求头带 Authorization: Bearer <token>（方式 A，token 由后端传入）；
      接口挂了/超时返回提示，绝不让问答崩掉。
    """
    if not ENABLE_FARM_API:
        return "（开发模式：假数据模拟，ENABLE_FARM_API 未开启）\n" + json.dumps(
            _FAKE_FARM_DATA, ensure_ascii=False, indent=2
        )

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(
            f"{FARM_API_BASE}/farms/{FARM_FARM_ID}/overview",
            headers=headers,
            timeout=3,
        )
        resp.raise_for_status()
        data = resp.json()
        # 后端返回整个农场所有地块的概况（数组）；给了 plot_id 就只保留该地块
        if plot_id and isinstance(data, list):
            data = [p for p in data if (p.get("plot") or {}).get("id") == plot_id]
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"（实时农场数据获取失败：{type(e).__name__}: {e}）"


# ===== ⑥ 多轮对话 + 问答 =====
session_store: dict[str, list] = {}   # session_id → [SystemMessage/HumanMessage/AIMessage...]


def ask(question: str, session_id: str = "default", user_id: str = "default",
        token: str = "", plot_id: str = "", farm_context: dict[str, Any] | None = None):
    """token/plot_id：对接后端 B 用。token 是后端传入的用户令牌（方式 A）；
    plot_id 是用户当前选的地块（如 P001），决定查哪块地的实时数据。"""
    history = session_store.setdefault(session_id, [])
    is_followup = bool(history)          # 同一会话里问过问题，就算追问

    # 1) 每轮确定性检索知识库
    if not MODEL_ENABLED:
        raise RuntimeError("AI model is not configured")
    docs = retriever.similarity_search(question, k=TOP_K)
    context = "\n\n".join(d.page_content for d in docs)

    # 2) 判断本问题类型（闲聊/足够/部分/不足）+ 是否需要实时农场数据；
    #    时效问题（最新/价格/行情…）直接联网，不用判断实时农场数据
    timely = is_timely_question(question)
    kind = None if timely else classify_question(question, context)
    needs_real = False
    if not timely:
        needs_real = needs_realtime(question)

    # 3) 按类型组装输入内容，并记录 refs（文献参考）
    refs = []
    if timely or (kind == "不足" and not is_followup):
        # 时效问题 或 首轮知识库没覆盖 → 联网搜索
        web_text = search_web(question)
        user_msg = HumanMessage(content=f"【联网搜索结果】\n{web_text}\n\n用户问题：{question}")
        refs.append({"source": "联网搜索(博查)", "text": web_text[:150]})
    elif kind == "闲聊":
        # 寒暄/打招呼 → 纯聊天，不检索不联网
        user_msg = HumanMessage(content=question)
    else:
        # 知识库足够直接答；部分相关 → 结合资料 + 农业常识推断（不联网）；
        # 追问（即使"不足"）→ 靠上一轮话题接着答，不强行联网
        if kind == "部分":
            extra = (
                "\n\n【说明】检索到的资料只与问题部分相关。请以资料为骨架，"
                "结合你的农业常识合理推断，给出完整、可操作的答案；"
                "推断的内容请明确标注（如\"（推断）\"或\"按一般经验\"），不要伪装成资料原文。"
            )
        else:
            extra = ""
        user_msg = HumanMessage(content=f"【私有知识库资料】\n{context}{extra}\n\n用户问题：{question}")
        if docs:
            source = docs[0].metadata.get("source", "农业知识库检索")
            refs.append({"source": source, "text": docs[0].page_content[:150]})

    # 3.5) 当前系统由主后端鉴权并传入地块上下文；旧接口仍可按需查询 overview。
    if farm_context:
        farm_text = json.dumps(farm_context, ensure_ascii=False, indent=2)
        user_msg.content += f"\n\n【当前地块实时数据】\n{farm_text}"
        refs.append({"source": "当前地块实时数据", "text": farm_text[:150]})
    elif needs_real:
        farm_text = query_farm_db(plot_id=plot_id, token=token)
        user_msg.content += f"\n\n【实时农场数据】\n{farm_text}"
        refs.append({"source": "实时农场数据(后端)", "text": farm_text[:150]})

    # 4) 大模型作答（纯对话，无工具 → 稳定，不会输出乱码），注入长期用户档案 + 长期记忆
    profile = load_profile(user_id)
    memories = load_memories(user_id)
    system_msg = SystemMessage(
        content=SYSTEM_PROMPT + "\n\n" + format_profile(profile) + "\n\n" + format_memories(memories)
    )
    messages = [system_msg] + history + [user_msg]
    answer = llm.invoke(messages).content
    answer = answer.replace("**", "")   # 兜底：去掉模型偶尔漏掉的 Markdown 加粗标记

    # 5) 记住这一轮（存原始问题，资料每轮重新查，不串味）
    session_store[session_id] = history + [
        HumanMessage(content=question),
        AIMessage(content=answer),
    ]

    # 6) 更新长期记忆（寒暄/闲聊不抽取，避免浪费调用）：档案去重合并 + 新记忆去重合并
    if kind != "闲聊":
        new_profile, new_mems = extract_memory_turn(question, profile, memories)
        save_profile(merge_profile(profile, new_profile), user_id)
        merged = list(memories)
        for m in new_mems:
            if not _is_dup(m, merged) and len(merged) < MAX_MEMORIES:
                merged.append(m)
        save_memories(merged, user_id)

    return {"answer": answer, "refs": refs}


# ===== ⑦ 对外接口 =====
app = FastAPI(title="农业灌溉 RAG 智能体（确定性检索 + 联网搜索）")

# CORS：允许前端网页跨域调用本服务（开发期放开全部来源，上线前按需收紧）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatReq(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str = "default"   # 同一个 session_id 算同一段对话
    user_id: str = "default"      # 用户唯一标识：档案/长期记忆按它隔离，不同用户互不共享
    token: str = ""               # 方式 A：后端调 RAG 时把当前用户 token 传过来（也可走请求头 Authorization）
    plot_id: str = ""             # 可选：用户当前选的地块，如 P001，决定查哪块地的实时数据


class ChatMessageReq(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    plotId: str | None = None
    userId: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    sessionId: str
    answer: str
    sources: list[str]


@app.post("/chat")
def chat(req: ChatReq):
    try:
        return ask(req.question, req.session_id, req.user_id, req.token, req.plot_id)
    except Exception as error:
        logger.exception("Legacy chat request failed")
        raise HTTPException(status_code=502, detail="AI_MODEL_REQUEST_FAILED") from error


@app.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def chat_message(session_id: str, req: ChatMessageReq) -> ChatMessageResponse:
    try:
        result = ask(
            req.message.strip(),
            session_id=session_id,
            user_id=req.userId or "default",
            plot_id=req.plotId or "",
            farm_context=req.context,
        )
    except Exception as error:
        logger.exception("Chat request failed for session %s", session_id)
        raise HTTPException(status_code=502, detail="AI_MODEL_REQUEST_FAILED") from error
    sources = list(dict.fromkeys(ref["source"] for ref in result["refs"]))
    return ChatMessageResponse(sessionId=session_id, answer=result["answer"], sources=sources)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "modelEnabled": MODEL_ENABLED,
        "model": LLM_MODEL if MODEL_ENABLED else None,
        "retrievalMode": RETRIEVAL_MODE,
        "vectorDatabaseReady": RETRIEVAL_MODE == "chroma",
    }


@app.get("/")
def root():
    return {
        "service": "农业灌溉 RAG 智能体（确定性检索 + 联网搜索）",
        "向量库": COLLECTION,
        "检索模式": RETRIEVAL_MODE,
        "模型已配置": MODEL_ENABLED,
        "检索topk": TOP_K,
        "活动会话数": len(session_store),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
