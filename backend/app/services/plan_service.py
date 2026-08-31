from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .stage_service import stage_bounds, validate_template_content


def _stage_periods(stages: list[dict[str, Any]], today: date, days: int = 365) -> list[dict[str, Any]]:
    periods: list[dict[str, Any]] = []
    window_end = today + timedelta(days=days)
    for stage in stages:
        for start_year in range(today.year - 1, window_end.year + 1):
            stage_start, stage_end = stage_bounds(stage, start_year)
            if stage_end < today or stage_start > window_end:
                continue
            periods.append({
                "stage": stage,
                "start": stage_start,
                "effectiveStart": max(stage_start, today),
                "end": min(stage_end, window_end),
            })
    return sorted(periods, key=lambda item: (item["effectiveStart"], -int(item["stage"].get("priority", 0))))


def preview_plan(
    template_content: Any,
    *,
    today: date,
    override_code: str | None = None,
) -> list[dict[str, Any]]:
    content = validate_template_content(template_content)
    stages: list[dict[str, Any]] = content["stages"]
    periods = _stage_periods(stages, today)
    if override_code:
        override = next((stage for stage in stages if stage["code"] == override_code), None)
        if override is None:
            raise ValueError("stage override is not present in the bound template")
        override_period = {
            "stage": override,
            "start": today,
            "effectiveStart": today,
            "end": next((end for start, end in (stage_bounds(override, today.year - 1), stage_bounds(override, today.year)) if start <= today <= end), today),
        }
        periods = [override_period] + [period for period in periods if period["effectiveStart"] > override_period["end"]]

    tasks: list[dict[str, Any]] = []
    for period_index, period in enumerate(periods):
        stage = period["stage"]
        stage_tasks = stage.get("tasks") if isinstance(stage.get("tasks"), list) else []
        current_generated = 0
        for template_task in stage_tasks:
            if not isinstance(template_task, dict):
                continue
            offset = max(int(template_task.get("offsetDays", 0)), 0)
            first_date = period["start"] + timedelta(days=offset)
            repeat_days = template_task.get("repeatDays")
            dates: list[date] = []
            if repeat_days and template_task.get("repeatUntilStageEnd"):
                repeat = max(int(repeat_days), 1)
                while first_date < today:
                    first_date += timedelta(days=repeat)
                while first_date <= period["end"]:
                    dates.append(first_date)
                    first_date += timedelta(days=repeat)
            elif first_date >= today and first_date <= period["end"]:
                dates.append(first_date)
            for planned_date in dates:
                tasks.append(
                    {
                        "stageCode": stage["code"],
                        "stageName": stage["name"],
                        "taskType": str(template_task.get("type") or "PATROL"),
                        "taskName": str(template_task.get("name") or f"{stage['name']}巡查"),
                        "plannedDate": planned_date.isoformat(),
                        "taskSource": "PLAN",
                    }
                )
                if period_index == 0:
                    current_generated += 1
        if period_index == 0 and current_generated == 0:
            tasks.append(
                {
                    "stageCode": stage["code"],
                    "stageName": stage["name"],
                    "taskType": "PATROL",
                    "taskName": f"{stage['name']}周期巡查",
                    "plannedDate": today.isoformat(),
                    "taskSource": "PLAN",
                }
            )
    unique: dict[tuple[str, str, str], dict[str, Any]] = {}
    for task in tasks:
        unique[(task["stageCode"], task["taskName"], task["plannedDate"])] = task
    return sorted(unique.values(), key=lambda item: (item["plannedDate"], item["taskName"]))
