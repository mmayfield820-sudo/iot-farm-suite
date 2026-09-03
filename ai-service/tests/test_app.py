from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))

import app as service  # noqa: E402


class AiServiceTests(unittest.TestCase):
    def test_health_reports_configured_model_and_retrieval_mode(self) -> None:
        body = service.health()

        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["modelEnabled"], service.MODEL_ENABLED)
        self.assertEqual(
            body["model"], service.LLM_MODEL if service.MODEL_ENABLED else None
        )
        self.assertIn(body["retrievalMode"], {"local", "chroma"})

    def test_local_retriever_returns_agriculture_content(self) -> None:
        documents = service.LocalKnowledgeRetriever(
            SERVICE_DIR / "农业知识来源" / "农业知识库.md"
        ).similarity_search("黄瓜结瓜期怎么浇水", k=1)

        self.assertEqual(len(documents), 1)
        self.assertTrue(
            "浇水" in documents[0].page_content or "灌溉" in documents[0].page_content
        )

    def test_current_backend_contract_maps_context_and_sources(self) -> None:
        result = {
            "answer": "建议先核对墒情。",
            "refs": [
                {"source": "农业知识库", "text": "a"},
                {"source": "农业知识库", "text": "b"},
                {"source": "当前地块实时数据", "text": "c"},
            ],
        }
        request = service.ChatMessageReq(
            message="现在需要浇水吗？",
            plotId="P001",
            userId="U001",
            context={"soilMoisture": 62},
        )

        with patch.object(service, "ask", return_value=result) as ask_mock:
            response = service.chat_message("session-1", request)

        self.assertEqual(response.sessionId, "session-1")
        self.assertEqual(response.sources, ["农业知识库", "当前地块实时数据"])
        ask_mock.assert_called_once_with(
            "现在需要浇水吗？",
            session_id="session-1",
            user_id="U001",
            plot_id="P001",
            farm_context={"soilMoisture": 62},
        )


if __name__ == "__main__":
    unittest.main()
