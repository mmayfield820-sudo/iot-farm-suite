# -*- coding: utf-8 -*-
"""
自定义 Embeddings：内部直接调原生 openai client（和 app.py 的 .kb_cache 用的同一个调用）。

为什么需要它：
    langchain_openai.OpenAIEmbeddings 发给硅基流动的请求和原生 client 不一致，
    导致同一个句子出来两套不同的向量（余弦相似度只有 0.248，正常应接近 1.0），
    检索结果自然就乱了。
    这里包一层，让 Chroma 也走原生 client，保证向量和 numpy 基线版完全一致。

用法：把本文件的 SiliconFlowEmbeddings 传给 Chroma：
    from custom_embeddings import SiliconFlowEmbeddings
    embeddings = SiliconFlowEmbeddings()
"""
import os
import sys

from openai import OpenAI
from langchain_core.embeddings import Embeddings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 真 key 在 local_secrets.py（本地，不入 Git）；没建就在环境变量里设
try:
    from local_secrets import SILICONFLOW_API_KEY
except ImportError:
    SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
API_KEY = SILICONFLOW_API_KEY
BASE_URL = "https://api.siliconflow.cn/v1"
EMBED_MODEL = "BAAI/bge-m3"

BATCH_SIZE = 32  # 每次请求最多送多少段文字


class SiliconFlowEmbeddings(Embeddings):
    """把原生 openai client 包成 langchain 能用的 Embeddings 接口。"""

    def __init__(self, model: str = EMBED_MODEL):
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
