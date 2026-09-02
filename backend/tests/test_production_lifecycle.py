from __future__ import annotations

import unittest
from datetime import date

from backend.app.main import production_year_bounds


class ProductionLifecycleTests(unittest.TestCase):
    def test_production_year_uses_fixed_boundaries(self) -> None:
        self.assertEqual(production_year_bounds(2026), (date(2025, 12, 1), date(2026, 11, 30)))

    def test_following_production_year_keeps_the_same_fixed_boundaries(self) -> None:
        self.assertEqual(production_year_bounds(2027), (date(2026, 12, 1), date(2027, 11, 30)))


if __name__ == "__main__":
    unittest.main()
