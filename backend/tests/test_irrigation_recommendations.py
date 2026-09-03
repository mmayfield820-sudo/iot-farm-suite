from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from backend.app.irrigation_recommendations import (
    build_irrigation_recommendation,
    target_moisture_reached,
)


NOW = datetime(2026, 9, 1, 8, 0, 0)


def recommendation(**overrides):
    values = {
        "now": NOW,
        "moisture": 25,
        "report_at": NOW - timedelta(minutes=2),
        "target_min": 35,
        "target_max": 50,
        "stage_name": "转色期",
        "device_bound": True,
        "device_online": True,
        "irrigation_active": False,
        "base_duration_minutes": 30,
        "minimum_interval_minutes": 60,
        "last_irrigation_at": None,
        "last_irrigation_minutes": None,
        "rain_probability": 20,
        "rainy_days": 0,
        "temperature": 28,
        "weather_available": True,
    }
    values.update(overrides)
    return build_irrigation_recommendation(**values)


class IrrigationRecommendationTests(unittest.TestCase):
    def test_offline_device_blocks_irrigation(self):
        result = recommendation(device_online=False)
        self.assertEqual(result["decision"], "check_device")
        self.assertIsNone(result["suggestedMinutes"])

    def test_moisture_in_target_range_needs_no_irrigation(self):
        result = recommendation(moisture=40)
        self.assertEqual(result["decision"], "no_irrigation")

    def test_high_rain_probability_delays_irrigation(self):
        result = recommendation(rain_probability=85)
        self.assertEqual(result["decision"], "wait")
        self.assertIn("降雨概率", result["summary"])

    def test_recent_irrigation_requires_recheck_for_small_deficit(self):
        result = recommendation(
            moisture=32,
            last_irrigation_at=NOW - timedelta(minutes=15),
            last_irrigation_minutes=20,
        )
        self.assertEqual(result["decision"], "wait")
        self.assertIn("上次灌溉", result["summary"])

    def test_duration_is_dynamically_increased_for_large_deficit_and_heat(self):
        result = recommendation(moisture=15, temperature=35)
        self.assertEqual(result["decision"], "irrigate")
        self.assertEqual(result["suggestedMinutes"], 45)
        self.assertIn("动态修正", result["summary"])

    def test_stale_sensor_data_blocks_recommendation(self):
        result = recommendation(report_at=NOW - timedelta(minutes=45))
        self.assertEqual(result["decision"], "check_data")

    def test_target_stop_uses_latest_reading(self):
        self.assertFalse(target_moisture_reached([34], 35))
        self.assertTrue(target_moisture_reached([36], 35))

    def test_target_stop_can_require_multiple_samples_when_requested(self):
        self.assertFalse(target_moisture_reached([36, 34], 35, required_samples=2))
        self.assertTrue(target_moisture_reached([36, 35], 35, required_samples=2))


if __name__ == "__main__":
    unittest.main()
