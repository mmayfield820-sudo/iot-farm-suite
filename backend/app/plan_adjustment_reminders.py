from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text


def affected_plan_tasks(connection: Any, *, plot_id: int, as_of: date) -> list[dict[str, Any]]:
    """Return upcoming irrigation or patrol work affected by a field condition."""
    rows = connection.execute(
        text(
            "SELECT t.task_id, t.title, t.task_type, t.scheduled_date "
            "FROM management_task t JOIN management_plan p ON p.plan_id = t.plan_id "
            "WHERE t.plot_id = :plot AND p.plan_status = 'active' "
            "AND t.task_status IN ('pending', 'in_progress') "
            "AND t.scheduled_date BETWEEN :start AND :end "
            "AND (LOWER(t.task_type) IN ('irrigation', 'patrol') "
            "OR t.task_type IN ('灌溉', '巡园', '巡查') "
            "OR t.title LIKE '%灌溉%' OR t.title LIKE '%巡园%' OR t.title LIKE '%巡查%') "
            "ORDER BY t.scheduled_date, t.task_id LIMIT 5"
        ),
        {"plot": plot_id, "start": as_of, "end": as_of + timedelta(days=7)},
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


def open_plan_adjustment_reminder(
    connection: Any,
    *,
    plot_id: int,
    reminder_type: str,
    description: str,
    tasks: list[dict[str, Any]],
    timestamp: datetime,
) -> int:
    """Keep one active reminder per plot and trigger type, refreshing its task snapshot."""
    dedupe_key = f"{reminder_type}:{plot_id}"
    result = connection.execute(
        text(
            "INSERT INTO plan_adjustment_reminder "
            "(plot_id, reminder_type, dedupe_key, reminder_description, triggered_at, reminder_status) "
            "VALUES (:plot, :type, :key, :description, :timestamp, 'active') "
            "ON DUPLICATE KEY UPDATE reminder_id = LAST_INSERT_ID(reminder_id), "
            "reminder_description = VALUES(reminder_description), triggered_at = VALUES(triggered_at), "
            "disposition_action = IF(reminder_status = 'recovered', NULL, disposition_action), "
            "disposition_note = IF(reminder_status = 'recovered', NULL, disposition_note), "
            "disposed_by = IF(reminder_status = 'recovered', NULL, disposed_by), "
            "disposed_at = IF(reminder_status = 'recovered', NULL, disposed_at), "
            "recovered_at = IF(reminder_status = 'recovered', NULL, recovered_at), "
            "reminder_status = IF(reminder_status = 'recovered', 'active', reminder_status)"
        ),
        {
            "plot": plot_id,
            "type": reminder_type,
            "key": dedupe_key,
            "description": description,
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


def recover_plan_adjustment_reminder(
    connection: Any,
    *,
    plot_id: int,
    reminder_type: str,
    timestamp: datetime,
) -> None:
    connection.execute(
        text(
            "UPDATE plan_adjustment_reminder SET reminder_status = 'recovered', recovered_at = :timestamp "
            "WHERE dedupe_key = :key AND reminder_status IN ('active', 'handled')"
        ),
        {"key": f"{reminder_type}:{plot_id}", "timestamp": timestamp},
    )


def sync_low_moisture_reminder(
    connection: Any,
    *,
    plot_id: int,
    moisture: float,
    lower_bound: float | None,
    stage_name: str | None,
    timestamp: datetime,
) -> None:
    if lower_bound is None or moisture >= lower_bound:
        recover_plan_adjustment_reminder(
            connection, plot_id=plot_id, reminder_type="low_moisture", timestamp=timestamp
        )
        return
    tasks = affected_plan_tasks(connection, plot_id=plot_id, as_of=timestamp.date())
    basis = f"{stage_name}墒情目标下限 {lower_bound:g}%" if stage_name else f"墒情阈值 {lower_bound:g}%"
    task_text = "、".join(task["title"] for task in tasks) if tasks else "未来 7 天暂无灌溉或巡园任务"
    open_plan_adjustment_reminder(
        connection,
        plot_id=plot_id,
        reminder_type="low_moisture",
        description=f"当前土壤湿度 {moisture:g}% 低于{basis}；受影响任务：{task_text}",
        tasks=tasks,
        timestamp=timestamp,
    )


def sync_device_offline_reminder(
    connection: Any,
    *,
    plot_id: int,
    device_code: str,
    timestamp: datetime,
) -> None:
    tasks = affected_plan_tasks(connection, plot_id=plot_id, as_of=timestamp.date())
    task_text = "、".join(task["title"] for task in tasks) if tasks else "未来 7 天暂无灌溉或巡园任务"
    open_plan_adjustment_reminder(
        connection,
        plot_id=plot_id,
        reminder_type="device_offline",
        description=f"设备 {device_code} 已离线；受影响任务：{task_text}",
        tasks=tasks,
        timestamp=timestamp,
    )


def sync_continuous_rain_reminder(
    connection: Any,
    *,
    plot_id: int,
    rainy_days: int,
    timestamp: datetime,
) -> None:
    if rainy_days < 2:
        recover_plan_adjustment_reminder(
            connection, plot_id=plot_id, reminder_type="continuous_rain", timestamp=timestamp
        )
        return
    tasks = affected_plan_tasks(connection, plot_id=plot_id, as_of=timestamp.date())
    task_text = "、".join(task["title"] for task in tasks) if tasks else "未来 7 天暂无灌溉或巡园任务"
    open_plan_adjustment_reminder(
        connection,
        plot_id=plot_id,
        reminder_type="continuous_rain",
        description=f"天气预报显示未来连续 {rainy_days} 天有降雨；受影响任务：{task_text}",
        tasks=tasks,
        timestamp=timestamp,
    )


def consecutive_rainy_days(forecast: Any) -> int:
    """Treat two forecast days with rain or a >=60% probability as continuous rain."""
    if not isinstance(forecast, list):
        return 0
    longest = current = 0
    for item in forecast:
        if not isinstance(item, dict):
            current = 0
            continue
        condition = str(item.get("condition") or item.get("weather") or "")
        raw_probability = (
            item.get("rainProbability")
            if item.get("rainProbability") is not None
            else item.get("rain_probability", item.get("precipitation_probability", 0))
        )
        try:
            probability = float(raw_probability)
        except (TypeError, ValueError):
            probability = 0
        if "雨" in condition or "rain" in condition.lower() or probability >= 60:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest
