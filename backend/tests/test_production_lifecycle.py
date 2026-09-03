from __future__ import annotations

import unittest
from datetime import date

from backend.app.main import (
    annual_stage_window,
    archive_page,
    decoded_json_object,
    management_record_type_for_task,
    production_year_bounds,
    stage_status_is_locked,
)


class ProductionLifecycleTests(unittest.TestCase):
    def test_production_year_uses_fixed_boundaries(self) -> None:
        self.assertEqual(production_year_bounds(2026), (date(2025, 12, 1), date(2026, 11, 30)))

    def test_following_production_year_keeps_the_same_fixed_boundaries(self) -> None:
        self.assertEqual(production_year_bounds(2027), (date(2026, 12, 1), date(2027, 11, 30)))

    def test_stage_window_uses_the_saved_duration(self) -> None:
        self.assertEqual(
            annual_stage_window("S1", 2026, date(2025, 12, 1), 62),
            (date(2025, 12, 1), date(2026, 1, 31)),
        )

    def test_custom_stage_window_uses_its_own_duration(self) -> None:
        self.assertEqual(
            annual_stage_window("flower_extension", 2026, date(2026, 4, 1), 45),
            (date(2026, 4, 1), date(2026, 5, 15)),
        )

    def test_historical_undispatched_stage_is_locked(self) -> None:
        self.assertTrue(stage_status_is_locked("not_dispatched"))
        self.assertTrue(stage_status_is_locked("active"))
        self.assertTrue(stage_status_is_locked("completed"))
        self.assertFalse(stage_status_is_locked("planned"))

    def test_management_record_types_preserve_task_sources(self) -> None:
        self.assertEqual(management_record_type_for_task("template"), "plan_task")
        self.assertEqual(management_record_type_for_task("temporary"), "temporary_task")
        self.assertEqual(management_record_type_for_task("ad_hoc"), "ad_hoc_task")
        self.assertEqual(management_record_type_for_task("historical_supplement"), "historical_supplement")

    def test_management_record_json_values_are_safe_to_render(self) -> None:
        self.assertEqual(decoded_json_object('{"reason":"field change"}'), {"reason": "field change"})
        self.assertEqual(decoded_json_object("invalid"), {})
        self.assertEqual(decoded_json_object(["not", "an", "object"]), {})

    def test_archive_categories_page_independently(self) -> None:
        records = [{"id": value} for value in range(1, 8)]
        self.assertEqual(
            archive_page(records, 2, 3),
            {"items": [{"id": 4}, {"id": 5}, {"id": 6}], "page": 2, "pageSize": 3, "total": 7},
        )


if __name__ == "__main__":
    unittest.main()
