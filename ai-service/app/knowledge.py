from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_KNOWN_TERMS = (
    "灌溉", "浇水", "湿度", "土壤", "温度", "告警", "报警", "设备",
    "离线", "在线", "趋势", "效果", "天气", "降雨", "阈值", "传感器",
)


@dataclass(frozen=True)
class KnowledgeDocument:
    title: str
    content: str
    source: str


class KnowledgeBase:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[1] / "knowledge-base"
        self.documents = self._load_documents()

    def search(self, query: str, limit: int = 3) -> list[KnowledgeDocument]:
        terms = self._terms(query)
        ranked = sorted(
            self.documents,
            key=lambda document: self._score(document, terms),
            reverse=True,
        )
        return ranked[:limit]

    def _load_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for path in sorted(self.root.glob("*.md")):
            content = path.read_text(encoding="utf-8").strip()
            sections = re.findall(
                r"^##\s+(.+?)\n(.*?)(?=^##\s+|\Z)",
                content,
                flags=re.MULTILINE | re.DOTALL,
            )
            for title, body in sections:
                title = title.strip()
                body = body.strip()
                documents.append(
                    KnowledgeDocument(
                        title=title,
                        content=body.strip() or title,
                        source=f"知识库：{title}",
                    )
                )
        if not documents:
            raise RuntimeError(f"No knowledge documents found in {self.root}")
        return documents

    @staticmethod
    def _terms(text: str) -> set[str]:
        normalized = text.lower()
        terms = {term for term in _KNOWN_TERMS if term in normalized}
        terms.update(re.findall(r"[a-z0-9_]{2,}", normalized))
        return terms or {normalized[:20]}

    @staticmethod
    def _score(document: KnowledgeDocument, terms: set[str]) -> int:
        haystack = f"{document.title}\n{document.content}".lower()
        return sum(haystack.count(term) for term in terms)
