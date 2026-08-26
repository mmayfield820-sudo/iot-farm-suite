# -*- coding: utf-8 -*-
"""
搭建 Chroma 向量库（教程 C3）
流程：farming book.txt → ①加载 → ②切块 → ③embedding → ④存入 Chroma → ⑤检索测试
运行一次即可，向量库会持久化到 vector_db/chroma/
"""
import os
import sys
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

# 用自定义 embedding（内部走原生 openai client，和 numpy 基线版一致）
from custom_embeddings import SiliconFlowEmbeddings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ===== ① 配置 =====
# 真 key 在 local_secrets.py（本地，不入 Git）；没建就在环境变量里设
try:
    from local_secrets import SILICONFLOW_API_KEY as API_KEY
except ImportError:
    API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
BASE_URL = "https://api.siliconflow.cn/v1"
EMBED_MODEL = "BAAI/bge-m3"

BOOK_PATH = Path(__file__).parent / "农业知识来源" / "farming book.txt"
PERSIST_DIR = Path(__file__).parent / "vector_db" / "chroma"

CHUNK_SIZE = 500       # 每块最多字数
CHUNK_OVERLAP = 100    # 块之间重叠字数

# ===== ② 加载文档 =====
loader = TextLoader(str(BOOK_PATH), encoding="utf-8")
docs = loader.load()
total_chars = sum(len(d.page_content) for d in docs)
print(f"[1/5] 加载文档：{len(docs)} 个文档，约 {total_chars} 字")

# ===== ③ 切块 =====
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)
splits = splitter.split_documents(docs)
print(f"[2/5] 切块：{len(splits)} 块")

# ===== ④ embedding =====
embeddings = SiliconFlowEmbeddings()

# ===== ⑤ 建库 + 持久化 =====
vectordb = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    collection_name="farming_book",
    persist_directory=str(PERSIST_DIR),
)
print(f"[3/5] 向量库已建立，保存到 {PERSIST_DIR}")

# ===== ⑥ 检索测试 =====
print("[4/5] 检索测试：")
for q in ["黄瓜结瓜盛期怎么浇水", "滴灌和漫灌哪个省水"]:
    res = vectordb.similarity_search(q, k=3)
    print(f"\n  问题：{q}")
    for i, doc in enumerate(res):
        print(f"    [{i+1}] {doc.page_content[:60]}...")

print("\n[5/5] 完成。以后可直接这样加载现成的向量库：")
print("  Chroma(persist_directory=..., embedding_function=embeddings)")
