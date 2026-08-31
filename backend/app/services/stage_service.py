from __future__ import annotations

import json
import calendar
from datetime import date
from typing import Any


def parse_template_content(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("templateContent must be a JSON object")


def validate_template_content(value: Any) -> dict[str, Any]:
    content = parse_template_content(value)
    stages = content.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError("templateContent.stages must be a non-empty array")
    seen: set[str] = set()
    for stage in stages:
        if not isinstance(stage, dict):
            raise ValueError("each stage must be an object")
        code = stage.get("code")
        name = stage.get("name")
        start_node = stage.get("start") if isinstance(stage.get("start"), dict) else {}
        end_node = stage.get("end") if isinstance(stage.get("end"), dict) else {}
        start = stage.get("startMonth", start_node.get("month"))
        end = stage.get("endMonth", end_node.get("month"))
        if not isinstance(code, str) or not code.strip() or code in seen:
            raise ValueError("stage code must be non-empty and unique")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("stage name is required")
        if not isinstance(start, int) or not isinstance(end, int) or not 1 <= start <= 12 or not 1 <= end <= 12:
            raise ValueError("stage startMonth/endMonth must be between 1 and 12")
        stage["startMonth"] = start
        stage["endMonth"] = end
        stage["startPeriod"] = str(stage.get("startPeriod") or start_node.get("period") or "EARLY").upper()
        stage["endPeriod"] = str(stage.get("endPeriod") or end_node.get("period") or "LATE").upper()
        seen.add(code)
    return content


def month_in_stage(month: int, start_month: int, end_month: int) -> bool:
    if start_month <= end_month:
        return start_month <= month <= end_month
    return month >= start_month or month <= end_month


def period_start_day(period: str) -> int:
    return {"EARLY": 1, "MID": 11, "LATE": 21}.get(period.upper(), 1)


def period_end_day(year: int, month: int, period: str) -> int:
    return {"EARLY": 10, "MID": 20, "LATE": calendar.monthrange(year, month)[1]}.get(
        period.upper(), calendar.monthrange(year, month)[1]
    )


def stage_bounds(stage: dict[str, Any], start_year: int) -> tuple[date, date]:
    start_month = int(stage["startMonth"])
    end_month = int(stage["endMonth"])
    end_year = start_year + (1 if start_month > end_month else 0)
    return (
        date(start_year, start_month, period_start_day(str(stage.get("startPeriod", "EARLY")))),
        date(end_year, end_month, period_end_day(end_year, end_month, str(stage.get("endPeriod", "LATE")))),
    )


def date_in_stage(day: date, stage: dict[str, Any]) -> bool:
    return any(start <= day <= end for start, end in (stage_bounds(stage, day.year - 1), stage_bounds(stage, day.year)))


def tree_age_years(planting_date: date | None, today: date) -> int | None:
    if planting_date is None:
        return None
    years = today.year - planting_date.year
    if (today.month, today.day) < (planting_date.month, planting_date.day):
        years -= 1
    return max(years, 0)


def resolve_stage(
    template_content: Any,
    *,
    today: date,
    planting_date: date | None = None,
    override_code: str | None = None,
) -> dict[str, Any]:
    content = validate_template_content(template_content)
    stages: list[dict[str, Any]] = content["stages"]
    stage = None
    source = "CALCULATED"
    if override_code:
        stage = next((item for item in stages if item["code"] == override_code), None)
        if stage is None:
            raise ValueError("stage override is not present in the bound template")
        source = "OVERRIDE"
    else:
        active = [item for item in stages if date_in_stage(today, item)]
        stage = max(active, key=lambda item: int(item.get("priority", 0))) if active else None
    return {
        "stageCode": stage.get("code") if stage else None,
        "stageName": stage.get("name") if stage else None,
        "stageSource": source if stage else "UNAVAILABLE",
        "treeAgeYears": tree_age_years(planting_date, today),
        "asOfDate": today.isoformat(),
        "stage": stage,
    }
