from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherProviderError(RuntimeError):
    pass


_cache: dict[str, tuple[datetime, dict[str, Any]]] = {}
_cache_lock = Lock()


def weather_code_label(code: Any) -> str:
    try:
        value = int(code)
    except (TypeError, ValueError):
        return "未知"
    if value == 0:
        return "晴"
    if value in {1, 2}:
        return "多云"
    if value == 3:
        return "阴"
    if value in {45, 48}:
        return "雾"
    if value in {51, 53, 55, 56, 57}:
        return "毛毛雨"
    if value in {61, 63, 66, 80, 81}:
        return "小雨"
    if value in {65, 67, 82}:
        return "大雨"
    if value in {71, 73, 77, 85}:
        return "小雪"
    if value in {75, 86}:
        return "大雪"
    if value in {95, 96, 99}:
        return "雷雨"
    return "未知"


def _request_json(url: str, timeout: float) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "IoT-farm-suite/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        raise WeatherProviderError("WEATHER_PROVIDER_UNAVAILABLE") from error


def _read_json(url: str, timeout: float) -> dict[str, Any]:
    result = _request_json(url, timeout)
    if not isinstance(result, dict):
        raise WeatherProviderError("WEATHER_PROVIDER_INVALID_RESPONSE")
    return result


def _nominatim_coordinates(query: str, timeout: float) -> tuple[float, float] | None:
    target = f"{NOMINATIM_URL}?{urlencode({'q': query, 'format': 'jsonv2', 'limit': 1, 'countrycodes': 'cn'})}"
    result = _request_json(target, timeout)
    if not isinstance(result, list) or not result:
        return None
    try:
        return float(result[0]["lat"]), float(result[0]["lon"])
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherProviderError("WEATHER_LOCATION_INVALID") from error


def _coordinates(city: str, province: str, address: str, timeout: float) -> tuple[float, float, str]:
    default_latitude = os.getenv("WEATHER_DEFAULT_LATITUDE", "").strip()
    default_longitude = os.getenv("WEATHER_DEFAULT_LONGITUDE", "").strip()
    if default_latitude and default_longitude:
        try:
            return float(default_latitude), float(default_longitude), city or address or "农场所在地"
        except ValueError as error:
            raise WeatherProviderError("WEATHER_DEFAULT_COORDINATES_INVALID") from error

    queries = list(dict.fromkeys(value.strip() for value in (city, f"{province}{city}", address) if value and value.strip()))
    location_query = address.strip() or f"{province}{city}".strip() or city.strip()
    contains_chinese = any("\u4e00" <= character <= "\u9fff" for character in location_query)
    if contains_chinese:
        coordinates = _nominatim_coordinates(location_query, timeout)
        if coordinates:
            return coordinates[0], coordinates[1], city or address or location_query

    for query in queries:
        target = f"{GEOCODING_URL}?{urlencode({'name': query, 'count': 1, 'language': 'zh', 'format': 'json', 'countryCode': 'CN'})}"
        result = _read_json(target, timeout)
        locations = result.get("results")
        if not isinstance(locations, list) or not locations:
            continue
        location = locations[0]
        try:
            latitude = float(location["latitude"])
            longitude = float(location["longitude"])
        except (KeyError, TypeError, ValueError) as error:
            raise WeatherProviderError("WEATHER_LOCATION_INVALID") from error
        display_name = city or str(location.get("name") or query)
        return latitude, longitude, display_name
    if location_query and not contains_chinese:
        coordinates = _nominatim_coordinates(location_query, timeout)
        if coordinates:
            return coordinates[0], coordinates[1], city or address or location_query
    raise WeatherProviderError("WEATHER_LOCATION_NOT_FOUND")


def _series_rows(series: Any, fields: dict[str, str]) -> list[dict[str, Any]]:
    if not isinstance(series, dict) or not isinstance(series.get("time"), list):
        return []
    rows: list[dict[str, Any]] = []
    for index, timestamp in enumerate(series["time"]):
        row: dict[str, Any] = {"time": timestamp}
        for output_key, source_key in fields.items():
            values = series.get(source_key)
            row[output_key] = values[index] if isinstance(values, list) and index < len(values) else None
        if "weatherCode" in row:
            row["condition"] = weather_code_label(row.pop("weatherCode"))
        rows.append(row)
    return rows


def _forecast_payload(raw: dict[str, Any], city: str, latitude: float, longitude: float) -> dict[str, Any]:
    current = raw.get("current")
    if not isinstance(current, dict):
        raise WeatherProviderError("WEATHER_PROVIDER_INVALID_RESPONSE")

    hourly = _series_rows(raw.get("hourly"), {
        "temperature": "temperature_2m",
        "rainProbability": "precipitation_probability",
        "weatherCode": "weather_code",
    })
    daily = _series_rows(raw.get("daily"), {
        "high": "temperature_2m_max",
        "low": "temperature_2m_min",
        "rainProbability": "precipitation_probability_max",
        "windSpeedMax": "wind_speed_10m_max",
        "weatherCode": "weather_code",
    })
    current_hour = str(current.get("time") or "")[:13]
    upcoming_hourly = [row for row in hourly if str(row["time"])[:13] >= current_hour][:24]
    hourly_probability = upcoming_hourly[0]["rainProbability"] if upcoming_hourly else 0
    today = daily[0] if daily else {}
    return {
        "current": {
            "city": city,
            "condition": weather_code_label(current.get("weather_code")),
            "temperature": current.get("temperature_2m"),
            "feelsLike": current.get("apparent_temperature"),
            "high": today.get("high"),
            "low": today.get("low"),
            "rainProbability": hourly_probability,
            "humidity": current.get("relative_humidity_2m"),
            "wind": f"{current.get('wind_speed_10m', 0):g} km/h",
            "windSpeed": current.get("wind_speed_10m"),
            "updatedAt": current.get("time"),
            "latitude": latitude,
            "longitude": longitude,
        },
        "hourly": upcoming_hourly,
        "daily": [
            {
                "date": row["time"],
                "condition": row.get("condition"),
                "high": row.get("high"),
                "low": row.get("low"),
                "rainProbability": row.get("rainProbability"),
                "windSpeedMax": row.get("windSpeedMax"),
            }
            for row in daily
        ],
    }


def open_meteo_forecast(*, city: str = "", province: str = "", address: str = "") -> dict[str, Any]:
    timeout = float(os.getenv("WEATHER_SERVICE_TIMEOUT_SECONDS", "10"))
    ttl_seconds = max(0, int(os.getenv("WEATHER_CACHE_TTL_SECONDS", "600")))
    cache_key = "|".join((province.strip(), city.strip(), address.strip()))
    now = datetime.now(UTC)
    with _cache_lock:
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < timedelta(seconds=ttl_seconds):
            return deepcopy(cached[1])

    latitude, longitude, display_name = _coordinates(city, province, address, timeout)
    target = f"{FORECAST_URL}?{urlencode({
        'latitude': latitude,
        'longitude': longitude,
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m',
        'hourly': 'temperature_2m,precipitation_probability,weather_code',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max',
        'timezone': 'Asia/Shanghai',
        'forecast_days': 7,
    })}"
    payload = _forecast_payload(_read_json(target, timeout), display_name, latitude, longitude)
    with _cache_lock:
        _cache[cache_key] = (now, payload)
    return deepcopy(payload)
