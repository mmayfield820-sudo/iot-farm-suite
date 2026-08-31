from __future__ import annotations

import unittest
from datetime import date

from backend.app.services.plan_service import preview_plan


TEMPLATE = {
    "stages": [
        {"code": "SPRING", "name": "春季", "startMonth": 2, "endMonth": 3, "tasks": [{"type": "ONCE", "name": "春季一次任务", "offsetDays": 5}]},
        {"code": "SUMMER", "name": "夏季", "startMonth": 4, "endMonth": 9, "tasks": [{"type": "PATROL", "name": "夏季巡查", "offsetDays": 0, "repeatDays": 14, "repeatUntilStageEnd": True}, {"type": "ONCE", "name": "已错过任务", "offsetDays": 1}]},
        {"code": "WINTER", "name": "采后", "startMonth": 10, "endMonth": 1, "tasks": [{"type": "CLEAN", "name": "采后清园", "offsetDays": 10}]},
    ]
}


class PlanServiceTest(unittest.TestCase):
    def test_skips_missed_one_time_tasks_and_keeps_future_tasks(self) -> None:
        tasks = preview_plan(TEMPLATE, today=date(2026, 8, 30))
        missed_named = [task for task in tasks if task["taskName"] == "已错过任务"]
        self.assertTrue(all(task["plannedDate"] >= "2027-01-01" for task in missed_named))
        self.assertTrue(any(task["taskName"] == "夏季巡查" for task in tasks))
        self.assertTrue(any(task["taskName"] == "采后清园" for task in tasks))
        self.assertTrue(all(task["plannedDate"] >= "2026-08-30" for task in tasks))

    def test_current_stage_without_remaining_template_task_gets_fallback(self) -> None:
        template = {"stages": [{"code": "ONLY", "name": "全年管理", "startMonth": 1, "endMonth": 12, "tasks": [{"type": "ONCE", "name": "年初任务", "offsetDays": 1}]}]}
        tasks = preview_plan(template, today=date(2026, 8, 30))
        self.assertEqual(tasks[0]["taskType"], "PATROL")
        self.assertEqual(tasks[0]["plannedDate"], "2026-08-30")

    def test_override_stage_is_used_for_current_period(self) -> None:
        tasks = preview_plan(TEMPLATE, today=date(2026, 8, 30), override_code="WINTER")
        self.assertTrue(tasks)
        self.assertEqual(tasks[0]["stageCode"], "WINTER")

    def test_period_based_overlapping_stages_both_generate_tasks(self) -> None:
        template = {"stages": [
            {"code": "SPRING", "name": "春季", "start": {"month": 2, "period": "EARLY"}, "end": {"month": 3, "period": "LATE"}, "tasks": [{"type": "PATROL", "name": "春梢巡查", "offsetDays": 0, "repeatDays": 14, "repeatUntilStageEnd": True}]},
            {"code": "POST", "name": "采后", "start": {"month": 2, "period": "LATE"}, "end": {"month": 4, "period": "MID"}, "priority": 100, "canOverlap": True, "tasks": [{"type": "CLEANUP", "name": "采后清园", "offsetDays": 0, "repeatDays": 14, "repeatUntilStageEnd": True}]},
        ]}
        tasks = preview_plan(template, today=date(2026, 2, 25))
        self.assertTrue(any(task["stageCode"] == "SPRING" for task in tasks))
        self.assertTrue(any(task["stageCode"] == "POST" for task in tasks))


if __name__ == "__main__":
    unittest.main()
