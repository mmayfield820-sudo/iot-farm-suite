# -*- coding: utf-8 -*-
"""
自定义 Embeddings：内部直接调用 OpenAI 兼容 embedding 接口。

为什么需要它：
    这里包一层，让建库和 Chroma 查询都走同一个原生 client，保证向量一致。

用法：把本文件的 SiliconFlowEmbeddings 传给 Chroma：
    from custom_embeddings import SiliconFlowEmbeddings
    embeddings = SiliconFlowEmbeddings()
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.embeddings import Embeddings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_KEY = os.getenv("AI_EMBEDDING_API_KEY") or os.getenv("AI_MODEL_API_KEY", "")
BASE_URL = os.getenv("AI_EMBEDDING_BASE_URL") or os.getenv("AI_MODEL_BASE_URL", "")
EMBED_MODEL = os.getenv("AI_EMBEDDING_MODEL", "text-embedding-v3")

BATCH_SIZE = 32  # 每次请求最多送多少段文字


class SiliconFlowEmbeddings(Embeddings):
    """将任意 OpenAI 兼容 embedding 服务包装为 LangChain 接口。"""

    def __init__(self, model: str = EMBED_MODEL):
        if not API_KEY or not BASE_URL:
            raise RuntimeError("AI embedding service is not configured")
        self.model = model
        self._client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        vecs = []
        for i in range(0, len(texts), BATCH_SIZE):
            resp = self._client.embeddings.create(
                model=self.model,
                input=texts[i:i + BATCH_SIZE],
            )
            vecs.extend(d.embedding for d in resp.data)
        return vecs

    # langchain 的两个必实现方法：存库用 documents，查询用 query
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]
