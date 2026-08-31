from __future__ import annotations

import unittest
from datetime import date

from backend.app.services.stage_service import resolve_stage, tree_age_years


TEMPLATE = {
    "stages": [
        {"code": "SPRING_GROWTH", "name": "萌芽与春季管理期", "startMonth": 2, "endMonth": 3},
        {"code": "FRUIT_EXPANSION", "name": "果实膨大与秋梢期", "startMonth": 7, "endMonth": 9},
        {"code": "MATURITY", "name": "转色成熟期", "startMonth": 10, "endMonth": 11},
        {"code": "HARVEST_POSTHARVEST", "name": "采收及采后管理期", "startMonth": 11, "endMonth": 2},
    ]
}


class StageServiceTest(unittest.TestCase):
    def test_tree_age_respects_anniversary(self) -> None:
        self.assertEqual(tree_age_years(date(2020, 9, 1), date(2026, 8, 30)), 5)
        self.assertEqual(tree_age_years(date(2020, 8, 1), date(2026, 8, 30)), 6)

    def test_calculates_annual_stage_from_current_month(self) -> None:
        result = resolve_stage(TEMPLATE, today=date(2026, 8, 30), planting_date=date(2018, 3, 15))
        self.assertEqual(result["stageCode"], "FRUIT_EXPANSION")
        self.assertEqual(result["stageSource"], "CALCULATED")
        self.assertEqual(result["treeAgeYears"], 8)

    def test_supports_cross_year_stage(self) -> None:
        january = resolve_stage(TEMPLATE, today=date(2027, 1, 10))
        december = resolve_stage(TEMPLATE, today=date(2026, 12, 10))
        self.assertEqual(january["stageCode"], "HARVEST_POSTHARVEST")
        self.assertEqual(december["stageCode"], "HARVEST_POSTHARVEST")

    def test_override_has_priority(self) -> None:
        result = resolve_stage(TEMPLATE, today=date(2026, 8, 30), override_code="MATURITY")
        self.assertEqual(result["stageCode"], "MATURITY")
        self.assertEqual(result["stageSource"], "OVERRIDE")

    def test_supports_period_based_template_and_overlap_priority(self) -> None:
        template = {"stages": [
            {"code": "SPRING", "name": "春季", "start": {"month": 2, "period": "EARLY"}, "end": {"month": 3, "period": "LATE"}, "priority": 50},
            {"code": "LATE_HARVEST", "name": "晚熟采收", "start": {"month": 2, "period": "LATE"}, "end": {"month": 4, "period": "MID"}, "priority": 100, "canOverlap": True},
        ]}
        self.assertEqual(resolve_stage(template, today=date(2026, 2, 10))["stageCode"], "SPRING")
        self.assertEqual(resolve_stage(template, today=date(2026, 2, 25))["stageCode"], "LATE_HARVEST")


if __name__ == "__main__":
    unittest.main()
