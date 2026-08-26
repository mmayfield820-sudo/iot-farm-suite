# -*- coding: utf-8 -*-
"""
博查（Bocha）联网搜索工具 —— 给 RAG 智能体的 agent 用。
当私有知识库没有收录问题时，agent 会调用这个工具在互联网上搜索。

用法：先在 https://open.bochaai.com 注册并获取 API Key（免费额度），
     把下面的 BOCHA_API_KEY 填上。不填也能跑——工具会返回"未配置"，
     让大模型走"资料不足→常识补充+引导提问"的兜底方案。
"""
import os
import sys

import requests
from langchain_core.tools import tool

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 真 key 在 local_secrets.py（本地，不入 Git）；没建就在环境变量里设 BOCHA_API_KEY
try:
    from local_secrets import BOCHA_API_KEY
except ImportError:
    BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "")
BOCHA_URL = "https://api.bochaai.com/v1/web-search"


def search_web(query: str, count: int = 5) -> str:
    """调用博查搜索 API，返回格式化的网页结果（标题+链接+摘要）。"""
    if not BOCHA_API_KEY:
        return "（联网搜索未配置：还没有设置博查 API Key，请先到 open.bochaai.com 注册获取后填入 web_search.py）"

    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"query": query, "summary": True, "count": count}

    try:
        resp = requests.post(BOCHA_URL, headers=headers, json=body, timeout=20)
    except Exception as e:
        return f"（联网搜索请求失败：{type(e).__name__}: {e}）"

    if resp.status_code != 200:
        return f"（联网搜索出错：HTTP {resp.status_code} {resp.text[:100]}）"

    data = resp.json().get("data", {})
    pages = data.get("webPages", {}).get("value", [])
    if not pages:
        return "（联网搜索无结果）"

    lines = []
    for p in pages:
        title = p.get("name", "")
        url = p.get("url", "")
        summary = p.get("summary") or p.get("snippet", "")
        lines.append(f"[{title}]\n{url}\n{summary}")
    return "\n\n".join(lines)


@tool
def web_search(query: str) -> str:
    """联网搜索工具。满足以下任一情况时必须调用本工具，否则先查私有知识库：
    1) 用户问题明确要求"最新""当前""今年/某年"等时效性信息；
    2) 私有知识库资料没有覆盖用户问题的答案。
    query 应写成简洁的中文搜索关键词。返回网页标题、链接和内容摘要。"""
    return search_web(query)
