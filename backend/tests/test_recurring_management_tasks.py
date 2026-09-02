from __future__ import annotations

import unittest
from datetime import date

from backend.app.main import recurring_task_dates


class RecurringManagementTaskTests(unittest.TestCase):
    def test_weekly_task_expands_through_stage_end(self) -> None:
        dates = recurring_task_dates(date(2026, 9, 1), date(2026, 9, 30), 7, True)

        self.assertEqual(
            dates,
            [
                date(2026, 9, 1),
                date(2026, 9, 8),
                date(2026, 9, 15),
                date(2026, 9, 22),
                date(2026, 9, 29),
            ],
        )

    def test_one_off_task_keeps_only_its_first_date(self) -> None:
        self.assertEqual(
            recurring_task_dates(date(2026, 9, 14), date(2026, 10, 31), None, False),
            [date(2026, 9, 14)],
        )

    def test_task_starting_after_stage_end_is_omitted(self) -> None:
        self.assertEqual(recurring_task_dates(date(2026, 10, 1), date(2026, 9, 30), 7, True), [])

    def test_recurring_task_rejects_missing_interval(self) -> None:
        with self.assertRaises(ValueError):
            recurring_task_dates(date(2026, 9, 1), date(2026, 9, 30), None, True)


if __name__ == "__main__":
    unittest.main()
