from __future__ import annotations

import unittest
from datetime import datetime

from backend.app.plan_adjustment_reminders import (
    consecutive_rainy_days,
    shanghai_day,
    shanghai_day_utc_bounds,
    task_is_affected,
    weather_reminder_conditions,
)


class WeatherReminderTests(unittest.TestCase):
    def test_shanghai_calendar_day_uses_utc_plus_eight(self):
        timestamp = datetime(2026, 8, 31, 16, 30)
        self.assertEqual(shanghai_day(timestamp).isoformat(), "2026-09-01")
        start, end = shanghai_day_utc_bounds(timestamp)
        self.assertEqual(start, datetime(2026, 8, 31, 16, 0))
        self.assertEqual(end, datetime(2026, 9, 1, 16, 0))

    def test_consecutive_rain_only_counts_from_today(self):
        forecast = [
            {"condition": "晴", "rainProbability": 10},
            {"condition": "小雨", "rainProbability": 80},
            {"condition": "中雨", "rainProbability": 90},
        ]
        self.assertEqual(consecutive_rainy_days(forecast), 0)

    def test_continuous_rain_suppresses_duplicate_high_probability_notice(self):
        forecast = {
            "current": {"windSpeed": 10},
            "hourly": [{"rainProbability": 90}],
            "daily": [
                {"condition": "小雨", "rainProbability": 80, "high": 28, "low": 18},
                {"condition": "中雨", "rainProbability": 75, "high": 27, "low": 17},
            ],
        }
        types = {item["type"] for item in weather_reminder_conditions(forecast)}
        self.assertIn("continuous_rain", types)
        self.assertNotIn("high_rain_probability", types)

    def test_single_rainy_day_creates_probability_notice(self):
        forecast = {
            "current": {"windSpeed": 10},
            "hourly": [{"rainProbability": 75}],
            "daily": [{"condition": "小雨", "rainProbability": 70, "high": 28, "low": 18}],
        }
        types = {item["type"] for item in weather_reminder_conditions(forecast)}
        self.assertEqual(types, {"high_rain_probability"})

    def test_tomorrow_hourly_rain_does_not_create_today_notice(self):
        forecast = {
            "current": {"windSpeed": 10},
            "hourly": [
                {"time": "2026-09-01T20:00", "rainProbability": 20},
                {"time": "2026-09-02T01:00", "rainProbability": 90},
            ],
            "daily": [
                {"date": "2026-09-01", "condition": "晴", "rainProbability": 20, "high": 28, "low": 18},
                {"date": "2026-09-02", "condition": "小雨", "rainProbability": 90, "high": 25, "low": 17},
            ],
        }
        self.assertEqual(weather_reminder_conditions(forecast), [])

    def test_temperature_frost_and_wind_conditions_are_supported(self):
        hot_and_windy = {
            "current": {"windSpeed": 42},
            "daily": [{"condition": "晴", "rainProbability": 5, "high": 36, "low": 20, "windSpeedMax": 45}],
        }
        cold = {
            "current": {"windSpeed": 5},
            "daily": [{"condition": "晴", "rainProbability": 5, "high": 9, "low": 1}],
        }
        hot_types = {item["type"] for item in weather_reminder_conditions(hot_and_windy)}
        cold_types = {item["type"] for item in weather_reminder_conditions(cold)}
        self.assertEqual(hot_types, {"high_temperature", "strong_wind"})
        self.assertEqual(cold_types, {"frost_risk"})

    def test_weather_notices_only_match_relevant_tasks(self):
        fertilizing = {"taskType": "fertilization", "title": "秋季施肥"}
        pruning = {"taskType": "pruning", "title": "果树修剪"}
        irrigation = {"taskType": "irrigation", "title": "检查滴灌"}
        self.assertTrue(task_is_affected(fertilizing, "high_rain_probability"))
        self.assertTrue(task_is_affected(pruning, "strong_wind"))
        self.assertFalse(task_is_affected(irrigation, "strong_wind"))
        self.assertTrue(task_is_affected(irrigation, "frost_risk"))


if __name__ == "__main__":
    unittest.main()
