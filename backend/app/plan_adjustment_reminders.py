from __future__ import annotations

import os
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import bindparam, text


SHANGHAI = timezone(timedelta(hours=8), "Asia/Shanghai")
WEATHER_REMINDER_TYPES = {
    "continuous_rain",
    "high_rain_probability",
    "high_temperature",
    "frost_risk",
    "strong_wind",
}
RAIN_TASK_KEYWORDS = {
    "irrigation", "patrol", "fertil", "spray", "pesticide", "harvest",
    "灌溉", "巡园", "巡查", "施肥", "喷药", "打药", "用药", "植保",
    "采收", "采摘", "除草", "清园", "套袋",
}
HEAT_TASK_KEYWORDS = {
    "patrol", "fertil", "spray", "pesticide", "prun", "harvest",
    "巡园", "巡查", "施肥", "喷药", "打药", "用药", "植保", "修剪",
    "采收", "采摘", "除草", "清园", "套袋",
}
WIND_TASK_KEYWORDS = {
    "patrol", "spray", "pesticide", "prun", "harvest",
    "巡园", "巡查", "喷药", "打药", "用药", "植保", "修剪", "采收",
    "采摘", "套袋",
}


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _threshold(name: str, default: float) -> float:
    value = _number(os.getenv(name))
    return default if value is None else value


def shanghai_day(timestamp: datetime) -> date:
    aware = timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
    return aware.astimezone(SHANGHAI).date()


def shanghai_day_utc_bounds(timestamp: datetime) -> tuple[datetime, datetime]:
    local_day = shanghai_day(timestamp)
    local_start = datetime.combine(local_day, time.min, tzinfo=SHANGHAI)
    start = local_start.astimezone(UTC).replace(tzinfo=None)
    return start, (local_start + timedelta(days=1)).astimezone(UTC).replace(tzinfo=None)


def consecutive_rainy_days(forecast: Any) -> int:
    """Count consecutive rainy forecast days beginning today."""
    if not isinstance(forecast, list):
        return 0
    count = 0
    for item in forecast:
        if not isinstance(item, dict):
            break
        condition = str(item.get("condition") or item.get("weather") or "")
        probability = _number(
            item.get("rainProbability")
            if item.get("rainProbability") is not None
            else item.get("rain_probability", item.get("precipitation_probability"))
        ) or 0
        if "雨" not in condition and "rain" not in condition.lower() and probability < 60:
            break
        count += 1
    return count


def weather_reminder_conditions(forecast: Any) -> list[dict[str, Any]]:
    """Return today's weather conditions that may affect field work."""
    if not isinstance(forecast, dict):
        return []
    current = forecast.get("current") if isinstance(forecast.get("current"), dict) else {}
    hourly = forecast.get("hourly") if isinstance(forecast.get("hourly"), list) else []
    daily = forecast.get("daily") if isinstance(forecast.get("daily"), list) else []
    today = daily[0] if daily and isinstance(daily[0], dict) else {}
    rainy_days = consecutive_rainy_days(daily)
    today_key = str(today.get("date") or today.get("time") or "")[:10]
    today_hourly = [
        item for item in hourly
        if isinstance(item, dict) and (not today_key or str(item.get("time") or "")[:10] == today_key)
    ]
    probabilities = [
        value for value in (
            _number(item.get("rainProbability"))
            for item in today_hourly[:24]
        ) if value is not None
    ]
    daily_rain = _number(today.get("rainProbability"))
    rain_probability = max(probabilities + ([daily_rain] if daily_rain is not None else []), default=0)
    high = _number(today.get("high", current.get("high")))
    low = _number(today.get("low", current.get("low")))
    wind_values = [
        value for value in (
            _number(current.get("windSpeed", current.get("wind_speed"))),
            _number(today.get("windSpeedMax", today.get("wind_speed_max"))),
        ) if value is not None
    ]
    wind_speed = max(wind_values, default=None)
    rain_threshold = _threshold("WEATHER_REMINDER_RAIN_PROBABILITY", 60)
    high_threshold = _threshold("WEATHER_REMINDER_HIGH_TEMPERATURE_C", 35)
    frost_threshold = _threshold("WEATHER_REMINDER_FROST_TEMPERATURE_C", 2)
    wind_threshold = _threshold("WEATHER_REMINDER_STRONG_WIND_KMH", 39)
    conditions: list[dict[str, Any]] = []

    if rainy_days >= 2:
        conditions.append({
            "type": "continuous_rain",
            "description": f"天气预报显示从今天起连续 {rainy_days} 天有降雨",
        })
    elif rain_probability >= rain_threshold:
        conditions.append({
            "type": "high_rain_probability",
            "description": f"今天最高降雨概率为 {rain_probability:g}%",
        })
    if high is not None and high >= high_threshold:
        conditions.append({
            "type": "high_temperature",
            "description": f"今天最高气温预计达到 {high:g}℃",
        })
    if low is not None and low <= frost_threshold:
        conditions.append({
            "type": "frost_risk",
            "description": f"今天最低气温预计为 {low:g}℃，存在低温霜冻风险",
        })
    if wind_speed is not None and wind_speed >= wind_threshold:
        conditions.append({
            "type": "strong_wind",
            "description": f"今天最大风速预计达到 {wind_speed:g} km/h，户外作业可能受到影响",
        })
    return conditions


def task_is_affected(task: dict[str, Any], reminder_type: str) -> bool:
    value = f"{task.get('taskType') or ''} {task.get('title') or ''}".lower()
    if reminder_type == "frost_risk":
        return True
    keywords = HEAT_TASK_KEYWORDS if reminder_type == "high_temperature" else WIND_TASK_KEYWORDS if reminder_type == "strong_wind" else RAIN_TASK_KEYWORDS
    return any(keyword in value for keyword in keywords)


def today_plan_tasks(connection: Any, *, plot_id: int, as_of: date) -> list[dict[str, Any]]:
    rows = connection.execute(
        text(
            "SELECT t.task_id, t.title, t.task_type, t.scheduled_date "
            "FROM management_task t JOIN management_plan p ON p.plan_id = t.plan_id "
            "WHERE t.plot_id = :plot AND p.plan_status = 'active' "
            "AND t.task_status IN ('pending', 'in_progress') AND t.scheduled_date = :today "
            "ORDER BY t.task_id"
        ),
        {"plot": plot_id, "today": as_of},
    ).mappings().all()
    return [
        {
            "taskId": row["task_id"],
            "title": row["title"],
            "taskType": row["task_type"],
            "scheduledDate": row["scheduled_date"],
        }
        for row in rows
    ]


def purge_non_today_reminders(connection: Any, *, timestamp: datetime) -> None:
    start, end = shanghai_day_utc_bounds(timestamp)
    stale_ids = text(
        "SELECT reminder_id FROM plan_adjustment_reminder "
        "WHERE triggered_at < :start OR triggered_at >= :end "
        "OR reminder_type NOT IN :weather_types"
    ).bindparams(bindparam("weather_types", expanding=True))
    params = {"start": start, "end": end, "weather_types": sorted(WEATHER_REMINDER_TYPES)}
    ids = connection.execute(stale_ids, params).scalars().all()
    if not ids:
        return
    connection.execute(
        text("DELETE FROM plan_adjustment_reminder_task WHERE reminder_id IN :ids").bindparams(bindparam("ids", expanding=True)),
        {"ids": ids},
    )
    connection.execute(
        text("DELETE FROM plan_adjustment_reminder WHERE reminder_id IN :ids").bindparams(bindparam("ids", expanding=True)),
        {"ids": ids},
    )


def _delete_today_reminder(
    connection: Any, *, plot_id: int, reminder_type: str, timestamp: datetime
) -> None:
    dedupe_key = f"{shanghai_day(timestamp).isoformat()}:{reminder_type}:{plot_id}"
    reminder_id = connection.execute(
        text("SELECT reminder_id FROM plan_adjustment_reminder WHERE dedupe_key = :key"),
        {"key": dedupe_key},
    ).scalar()
    if reminder_id is None:
        return
    connection.execute(
        text("DELETE FROM plan_adjustment_reminder_task WHERE reminder_id = :reminder"),
        {"reminder": reminder_id},
    )
    connection.execute(
        text("DELETE FROM plan_adjustment_reminder WHERE reminder_id = :reminder"),
        {"reminder": reminder_id},
    )


def _upsert_today_reminder(
    connection: Any,
    *,
    plot_id: int,
    reminder_type: str,
    description: str,
    tasks: list[dict[str, Any]],
    timestamp: datetime,
) -> int:
    dedupe_key = f"{shanghai_day(timestamp).isoformat()}:{reminder_type}:{plot_id}"
    task_text = "、".join(task["title"] for task in tasks)
    result = connection.execute(
        text(
            "INSERT INTO plan_adjustment_reminder "
            "(plot_id, reminder_type, dedupe_key, reminder_description, triggered_at, reminder_status) "
            "VALUES (:plot, :type, :key, :description, :timestamp, 'active') "
            "ON DUPLICATE KEY UPDATE reminder_id = LAST_INSERT_ID(reminder_id), "
            "reminder_description = VALUES(reminder_description), reminder_status = 'active'"
        ),
        {
            "plot": plot_id,
            "type": reminder_type,
            "key": dedupe_key,
            "description": f"{description}；可能影响今天的{task_text}任务，请结合现场情况合理安排。",
            "timestamp": timestamp,
        },
    )
    reminder_id = int(result.lastrowid)
    connection.execute(
        text("DELETE FROM plan_adjustment_reminder_task WHERE reminder_id = :reminder"),
        {"reminder": reminder_id},
    )
    for task in tasks:
        connection.execute(
            text(
                "INSERT INTO plan_adjustment_reminder_task "
                "(reminder_id, task_id, task_title, task_type, scheduled_date) "
                "VALUES (:reminder, :task, :title, :type, :scheduled)"
            ),
            {
                "reminder": reminder_id,
                "task": task["taskId"],
                "title": task["title"],
                "type": task["taskType"],
                "scheduled": task["scheduledDate"],
            },
        )
    return reminder_id


def sync_weather_reminders(
    connection: Any,
    *,
    plot_id: int,
    forecast: Any,
    timestamp: datetime,
) -> None:
    purge_non_today_reminders(connection, timestamp=timestamp)
    tasks = today_plan_tasks(connection, plot_id=plot_id, as_of=shanghai_day(timestamp))
    conditions = {item["type"]: item for item in weather_reminder_conditions(forecast)}
    for reminder_type in WEATHER_REMINDER_TYPES:
        condition = conditions.get(reminder_type)
        affected = [task for task in tasks if task_is_affected(task, reminder_type)] if condition else []
        if not affected:
            _delete_today_reminder(
                connection,
                plot_id=plot_id,
                reminder_type=reminder_type,
                timestamp=timestamp,
            )
            continue
        _upsert_today_reminder(
            connection,
            plot_id=plot_id,
            reminder_type=reminder_type,
            description=condition["description"],
            tasks=affected,
            timestamp=timestamp,
        )
