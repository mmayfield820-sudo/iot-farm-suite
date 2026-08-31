from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


MOCK_SCENARIOS: dict[str, dict[str, Any]] = {
    "SUNNY": {"currentTemperature": 30, "weather": "晴", "rainProbability24h": 10, "rainfall24h": 0},
    "RAINY": {"currentTemperature": 24, "weather": "中雨", "rainProbability24h": 85, "rainfall24h": 18},
    "HEAVY_RAIN": {"currentTemperature": 22, "weather": "暴雨", "rainProbability24h": 98, "rainfall24h": 62},
}


class WeatherService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def _mode(self) -> str:
        return os.getenv("WEATHER_MODE", "mock").lower()

    def _ttl_seconds(self) -> int:
        return max(int(os.getenv("WEATHER_CACHE_MINUTES", "15")), 0) * 60

    @staticmethod
    def _unavailable(message: str = "天气数据暂不可用") -> dict[str, Any]:
        return {"available": False, "message": message}

    def get_forecast(self, plot_id: int, location: str) -> dict[str, Any]:
        return self.get_forecast_by_location(location, cache_key=f"plot:{plot_id}:{location}")

    def get_forecast_by_location(self, location: str, *, cache_key: str | None = None) -> dict[str, Any]:
        mode = self._mode()
        key = f"{mode}:{cache_key or location}:{os.getenv('WEATHER_MOCK_SCENARIO', 'SUNNY')}"
        cached = self._cache.get(key)
        if cached and cached[0] > time.monotonic():
            return {**cached[1], "cached": True}
        result = self._mock(location) if mode == "mock" else self._api(location) if mode == "api" else self._unavailable("无效的天气服务模式")
        if result.get("available") and self._ttl_seconds() > 0:
            self._cache[key] = (time.monotonic() + self._ttl_seconds(), result)
        return result

    def _mock(self, location: str) -> dict[str, Any]:
        scenario = os.getenv("WEATHER_MOCK_SCENARIO", "SUNNY").upper()
        if scenario == "API_ERROR":
            return self._unavailable()
        data = MOCK_SCENARIOS.get(scenario, MOCK_SCENARIOS["SUNNY"])
        return {
            "source": "mock",
            "scenario": scenario if scenario in MOCK_SCENARIOS else "SUNNY",
            "location": location,
            **data,
            "forecastUpdatedAt": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "available": True,
            "cached": False,
        }

    def _api(self, location: str) -> dict[str, Any]:
        endpoint = os.getenv("WEATHER_API_URL", "").strip()
        if not endpoint:
            return self._unavailable("天气 API 未配置")
        target = f"{endpoint}{'&' if '?' in endpoint else '?'}{urlencode({'location': location})}"
        try:
            with urlopen(target, timeout=float(os.getenv("WEATHER_SERVICE_TIMEOUT_SECONDS", "10"))) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
            return self._unavailable()
        if not isinstance(payload, dict):
            return self._unavailable()
        current = payload.get("current", payload)
        try:
            return {
                "source": "api",
                "location": payload.get("location") or location,
                "currentTemperature": float(current["currentTemperature"]),
                "weather": str(current["weather"]),
                "rainProbability24h": float(current.get("rainProbability24h", 0)),
                "rainfall24h": float(current.get("rainfall24h", 0)),
                "forecastUpdatedAt": current.get("forecastUpdatedAt") or datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "available": True,
                "cached": False,
            }
        except (KeyError, TypeError, ValueError):
            return self._unavailable("天气 API 返回格式无效")


weather_service = WeatherService()
