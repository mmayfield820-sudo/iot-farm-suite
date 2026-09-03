from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from langchain_core.documents import Document


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


class LocalKnowledgeRetriever:
    """Zero-network fallback used until the optional Chroma index is built."""

    def __init__(self, source: Path) -> None:
        self.source = source
        self.documents = self._load(source)

    def similarity_search(self, query: str, k: int = 3) -> list[Document]:
        normalized_query = query.lower()
        query_tokens = Counter(_TOKEN_PATTERN.findall(normalized_query))
        ranked = sorted(
            self.documents,
            key=lambda document: self._score(document.page_content, normalized_query, query_tokens),
            reverse=True,
        )
        return ranked[:k]

    @staticmethod
    def _load(source: Path) -> list[Document]:
        text = source.read_text(encoding="utf-8")
        sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        documents = []
        for section in sections:
            content = section.strip()
            if not content or content.startswith("# ") and "\n## " not in content:
                continue
            title = content.splitlines()[0].lstrip("# ").strip()
            documents.append(
                Document(
                    page_content=content,
                    metadata={"source": f"本地农业知识库：{title}"},
                )
            )
        if not documents:
            raise RuntimeError(f"No knowledge documents found in {source}")
        return documents

    @staticmethod
    def _score(content: str, query: str, query_tokens: Counter[str]) -> int:
        content_tokens = Counter(_TOKEN_PATTERN.findall(content.lower()))
        unigram_score = sum(min(count, content_tokens[token]) for token, count in query_tokens.items())
        query_text = "".join(_TOKEN_PATTERN.findall(query))
        bigrams = {query_text[index:index + 2] for index in range(max(0, len(query_text) - 1))}
        return unigram_score + 4 * sum(content.count(bigram) for bigram in bigrams)
