# -*- coding: utf-8 -*-
"""
向量检索演示（教程 C3 第5步）。
三种检索方式 + 效果评估：
    1. similarity_search                —— 最普通的相似检索
    2. similarity_search_with_score     —— 带相似度分数
    3. max_marginal_relevance_search    —— MMR，兼顾相似度+多样性（防重复）
用法：
    python retrieve.py 番茄什么时候浇水    # 只看一个问题，对比三种方式
    python retrieve.py                    # 跑内置的 6 个问题，做效果评估
"""
import sys

from langchain_chroma import Chroma
from custom_embeddings import SiliconFlowEmbeddings

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

vectordb = Chroma(
    persist_directory="vector_db/chroma",
    collection_name="farming_book",
    embedding_function=SiliconFlowEmbeddings(),
)

# 覆盖不同章节的测试问题，用来检验检索效果
TEST_QUESTIONS = [
    "水肥一体化有什么好处",
    "滴灌设备由哪几部分组成",
    "黄瓜结瓜盛期怎么浇水",
    "番茄定植后什么时候浇缓苗水",
    "化肥怎么通过滴灌系统施到地里",
    "灌溉水到作物的根区需要什么",
]


def show(q: str):
    print("=" * 60)
    print(f"问题：{q}")
    print("=" * 60)

    # ① 最普通
    print("\n[1] similarity_search（不带分数）:")
    for i, doc in enumerate(vectordb.similarity_search(q, k=3)):
        print(f"    {i+1}. {doc.page_content[:55]}...")

    # ② 带分数（Chroma 返回的是 L2 距离，越小越像）
    print("\n[2] similarity_search_with_score（带距离）:")
    for i, (doc, score) in enumerate(vectordb.similarity_search_with_score(q, k=3)):
        print(f"    {i+1}. 距离={score:.4f}  {doc.page_content[:55]}...")

    # ③ MMR：多拉几个候选，再挑"又像又不重复"的
    print("\n[3] max_marginal_relevance_search（MMR，防重复）:")
    for i, doc in enumerate(vectordb.max_marginal_relevance_search(q, k=3, fetch_k=10)):
        print(f"    {i+1}. {doc.page_content[:55]}...")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 单独问一个问题
        show(" ".join(sys.argv[1:]))
    else:
        # 效果评估：每个问题只跑最普通的检索，取第 1 块，看是否相关
        print("【检索效果评估】每个问题看检索到的第 1 块是否相关\n")
        for q in TEST_QUESTIONS:
            top = vectordb.similarity_search(q, k=1)[0]
            print(f"问题：{q}")
            print(f"  → 命中：{top.page_content[:65]}...")
            print()
