from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


BOCHA_URL = "https://api.bochaai.com/v1/web-search"
TIMELY_KEYWORDS = (
    "今天", "明天", "近期", "最新", "实时", "当前天气", "天气", "气温",
    "降雨", "降水", "价格", "行情", "新闻",
)


def search_enabled() -> bool:
    return bool(os.getenv("BOCHA_API_KEY", "").strip())


def should_search(question: str) -> bool:
    text = question.strip()
    return any(keyword in text for keyword in TIMELY_KEYWORDS) or bool(re.search(r"20\d{2}年", text))


def build_search_query(question: str, context: dict[str, Any]) -> str:
    is_weather = any(keyword in question for keyword in ("天气", "气温", "降雨", "降水"))
    location = str(
        context.get("farmCity")
        or context.get("farmAddress")
        or context.get("location")
        or ""
    ).strip()
    if is_weather:
        local_now = datetime.now(ZoneInfo(os.getenv("AI_LOCAL_TIMEZONE", "Asia/Shanghai")))
        target_date = local_now + timedelta(days=1) if "明天" in question else local_now
        date_hint = target_date.strftime("%Y年%m月%d日") if any(word in question for word in ("今天", "明天")) else ""
        return " ".join(part for part in (location, date_hint, question.strip()) if part)
    return question.strip()


def search_web(query: str, count: int = 5) -> dict[str, Any]:
    queried_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    local_time = datetime.now(ZoneInfo(os.getenv("AI_LOCAL_TIMEZONE", "Asia/Shanghai"))).isoformat()
    api_key = os.getenv("BOCHA_API_KEY", "").strip()
    response: dict[str, Any] = {
        "attempted": True,
        "success": False,
        "provider": "bocha",
        "query": query,
        "queriedAt": queried_at,
        "queryLocalTime": local_time,
        "results": [],
        "error": "",
    }
    if not api_key:
        response["error"] = "未配置 BOCHA_API_KEY"
        return response

    payload = json.dumps(
        {"query": query, "summary": True, "count": max(1, min(count, 10))},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        BOCHA_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=float(os.getenv("BOCHA_TIMEOUT_SECONDS", "120"))) as raw_response:
            body = json.loads(raw_response.read().decode("utf-8"))
    except HTTPError as error:
        response["error"] = f"搜索服务返回 HTTP {error.code}"
        return response
    except (URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as error:
        response["error"] = f"搜索请求失败：{type(error).__name__}"
        return response

    pages = body.get("data", {}).get("webPages", {}).get("value", [])
    if not isinstance(pages, list):
        response["error"] = "搜索服务返回格式不正确"
        return response

    results = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        url = str(page.get("url") or "").strip()
        if urlparse(url).scheme not in {"http", "https"}:
            continue
        results.append(
            {
                "title": str(page.get("name") or "未命名网页").strip()[:200],
                "url": url,
                "snippet": str(page.get("summary") or page.get("snippet") or "").strip()[:1200],
            }
        )

    response["results"] = results
    response["success"] = bool(results)
    if not results:
        response["error"] = "联网搜索没有返回可用结果"
    return response
