from __future__ import annotations

import unittest

from backend.app.services.plan_change_service import json_value


class PlanChangeServiceTests(unittest.TestCase):
    def test_json_value_accepts_database_json_text(self) -> None:
        self.assertEqual(json_value('{"status":"PENDING_REVIEW"}'), {"status": "PENDING_REVIEW"})

    def test_json_value_keeps_native_mapping(self) -> None:
        value = {"plan": {"taskIds": [1, 2]}}
        self.assertIs(json_value(value), value)

    def test_json_value_keeps_null(self) -> None:
        self.assertIsNone(json_value(None))


if __name__ == "__main__":
    unittest.main()
