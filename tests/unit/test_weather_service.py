from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend.app.services.weather_service import WeatherService


class WeatherServiceTest(unittest.TestCase):
    def test_mock_sunny_and_cache(self) -> None:
        with patch.dict(os.environ, {"WEATHER_MODE": "mock", "WEATHER_MOCK_SCENARIO": "SUNNY", "WEATHER_CACHE_MINUTES": "15"}, clear=False):
            service = WeatherService()
            first = service.get_forecast(1, "重庆市奉节县")
            second = service.get_forecast(1, "重庆市奉节县")
        self.assertTrue(first["available"])
        self.assertEqual(first["rainfall24h"], 0)
        self.assertTrue(second["cached"])

    def test_mock_heavy_rain(self) -> None:
        with patch.dict(os.environ, {"WEATHER_MODE": "mock", "WEATHER_MOCK_SCENARIO": "HEAVY_RAIN", "WEATHER_CACHE_MINUTES": "0"}, clear=False):
            result = WeatherService().get_forecast(1, "重庆市奉节县")
        self.assertGreaterEqual(result["rainfall24h"], 50)
        self.assertGreaterEqual(result["rainProbability24h"], 90)

    def test_mock_api_error_degrades_explicitly(self) -> None:
        with patch.dict(os.environ, {"WEATHER_MODE": "mock", "WEATHER_MOCK_SCENARIO": "API_ERROR"}, clear=False):
            result = WeatherService().get_forecast(1, "重庆市奉节县")
        self.assertFalse(result["available"])
        self.assertEqual(result["message"], "天气数据暂不可用")

    def test_api_mode_without_url_degrades(self) -> None:
        with patch.dict(os.environ, {"WEATHER_MODE": "api", "WEATHER_API_URL": ""}, clear=False):
            result = WeatherService().get_forecast(1, "重庆市奉节县")
        self.assertFalse(result["available"])


if __name__ == "__main__":
    unittest.main()
