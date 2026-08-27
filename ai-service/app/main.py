from __future__ import annotations

import json
import logging
import os
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .knowledge import KnowledgeBase, KnowledgeDocument


load_dotenv()
logger = logging.getLogger(__name__)
knowledge_base = KnowledgeBase()
session_history: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=6))


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    plotId: str | None = None
    userId: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    sessionId: str
    answer: str
    sources: list[str]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Loaded %s agriculture knowledge sections", len(knowledge_base.documents))
    yield


app = FastAPI(title="Smart Farm AI Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "knowledgeDocuments": len(knowledge_base.documents),
        "modelEnabled": bool(os.getenv("AI_MODEL_BASE_URL") and os.getenv("AI_MODEL_API_KEY")),
    }


@app.post("/chat/sessions/{session_id}/messages", response_model=ChatResponse)
def chat(session_id: str, request: ChatRequest) -> ChatResponse:
    question = request.message.strip()
    documents = knowledge_base.search(question)
    answer = generate_answer(question, request.context, documents, list(session_history[session_id]))
    sources = list(dict.fromkeys(document.source for document in documents))
    session_history[session_id].append({"role": "user", "content": question})
    session_history[session_id].append({"role": "assistant", "content": answer})
    return ChatResponse(sessionId=session_id, answer=answer, sources=sources)


def generate_answer(
    question: str,
    context: dict[str, Any],
    documents: list[KnowledgeDocument],
    history: list[dict[str, str]],
) -> str:
    model_answer = generate_model_answer(question, context, documents, history)
    if model_answer:
        return model_answer
    return generate_rule_answer(question, context, documents)


def generate_rule_answer(
    question: str,
    context: dict[str, Any],
    documents: list[KnowledgeDocument],
) -> str:
    plot_name = context.get("plotName") or "当前地块"
    humidity = _number(context.get("soilMoisture"))
    threshold = _number(context.get("soilMoistureThreshold"))
    temperature = _number(context.get("temperature"))
    controller_online = context.get("irrigationDeviceOnline")
    irrigation_state = context.get("irrigationState")

    facts: list[str] = []
    if humidity is not None:
        facts.append(f"土壤湿度 {humidity:g}%")
    if threshold is not None:
        facts.append(f"告警阈值 {threshold:g}%")
    if temperature is not None:
        facts.append(f"环境温度 {temperature:g}℃")

    if humidity is not None and threshold is not None:
        if humidity < threshold:
            if controller_online is True:
                recommendation = "湿度低于阈值，建议在确认土壤和天气条件后安排短时灌溉。"
            else:
                recommendation = "湿度低于阈值，但灌溉控制器未在线；请先恢复设备通信，再进行人工确认。"
        else:
            recommendation = "当前湿度未低于阈值，暂不建议仅因湿度立即开启灌溉。"
    else:
        recommendation = "当前未取得完整地块实时数据，建议先核对温湿度和设备在线状态后再决定灌溉。"

    if irrigation_state == "on":
        recommendation += " 设备当前显示为灌溉中，请结合现场情况决定是否关闭。"
    if controller_online is False and "未在线" not in recommendation:
        recommendation += " 灌溉控制器当前离线，不能远程下发控制命令。"

    knowledge_hint = documents[0].content.split("\n")[0] if documents else ""
    context_text = "、".join(facts) if facts else "暂无完整实时数据"
    return f"{plot_name}：{context_text}。{recommendation} 参考建议：{knowledge_hint} 所有开关操作仍需在灌溉页面二次确认。"


def generate_model_answer(
    question: str,
    context: dict[str, Any],
    documents: list[KnowledgeDocument],
    history: list[dict[str, str]],
) -> str | None:
    base_url = os.getenv("AI_MODEL_BASE_URL", "").rstrip("/")
    api_key = os.getenv("AI_MODEL_API_KEY", "")
    model = os.getenv("AI_MODEL_NAME", "")
    if not base_url or not api_key or not model:
        return None

    retrieved = "\n\n".join(f"[{item.title}]\n{item.content}" for item in documents)
    system = (
        "你是智慧农业灌溉助手。只能依据提供的地块数据和知识库回答；"
        "数据不足时明确说明。不得声称已经控制设备，不得跳过用户二次确认。"
    )
    user_content = json.dumps(
        {"question": question, "plotContext": context, "knowledge": retrieved},
        ensure_ascii=False,
    )
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [{"role": "system", "content": system}, *history, {"role": "user", "content": user_content}],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    target = f"{base_url}/chat/completions"
    try:
        with urlopen(
            Request(target, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}),
            timeout=float(os.getenv("AI_MODEL_TIMEOUT_SECONDS", "15")),
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
        answer = body["choices"][0]["message"]["content"].strip()
        return answer or None
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        logger.warning("Model request failed with HTTP %s; using rule answer: %s", error.code, detail)
        return None
    except (URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError, OSError) as error:
        logger.warning("Model request failed; using rule answer: %s", error)
        return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
