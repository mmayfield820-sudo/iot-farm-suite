# -*- coding: utf-8 -*-
"""
查看 Chroma 向量库：库里存了什么、怎么检索。
用法：
    python view_vector_db.py               # 查看库信息 + 前几块原文
    python view_vector_db.py 滴灌怎么节水   # 带一个问题，跑相似度检索
"""
import sys

from langchain_chroma import Chroma
from custom_embeddings import SiliconFlowEmbeddings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VECTOR_DIR = "vector_db/chroma"
COLLECTION = "farming_book"

vectordb = Chroma(
    persist_directory=VECTOR_DIR,
    collection_name=COLLECTION,
    embedding_function=SiliconFlowEmbeddings(),
)

# 取库里的数据（documents + ids + metadatas）
data = vectordb.get(limit=100000)
n = len(data["ids"])
print(f"库里共有 {n} 块知识文本")

if len(sys.argv) < 2:
    # ===== 只看库：打印前 3 块的原文 =====
    print("\n前 3 块内容：\n" + "=" * 50)
    for i, doc in enumerate(data["documents"][:3]):
        print(f"\n—— 第 {i+1} 块 ——")
        print(doc[:120], "…" if len(doc) > 120 else "")
else:
    # ===== 带问题：相似度检索 =====
    q = " ".join(sys.argv[1:])
    print(f"\n问题：{q}\n" + "=" * 50)
    res = vectordb.similarity_search_with_score(q, k=3)
    for i, (doc, score) in enumerate(res):
        print(f"\n—— 第 {i+1} 块（相似度 {score:.4f}）——")
        print(doc.page_content[:120], "…" if len(doc.page_content) > 120 else "")
