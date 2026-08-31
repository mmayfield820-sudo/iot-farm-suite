from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import text

from .plan_adjustment_reminders import sync_low_moisture_reminder


def current_moisture_rule(
    connection: Any,
    *,
    plot_id: int,
    fallback_threshold: float | None,
    as_of: date,
) -> dict[str, Any]:
    """Resolve the moisture bounds that apply to a plot on the given date."""
    profile = connection.execute(
        text(
            "SELECT p.template_version_id, p.planting_date "
            "FROM plot pl JOIN farm_production_profile p ON p.farm_id = pl.farm_id "
            "WHERE pl.plot_id = :plot"
        ),
        {"plot": plot_id},
    ).mappings().first()
    if profile is not None:
        stages = connection.execute(
            text(
                "SELECT stage_code, stage_name, duration_days, moisture_min, moisture_max "
                "FROM growth_stage_template WHERE template_version_id = :version "
                "ORDER BY sort_order"
            ),
            {"version": profile["template_version_id"]},
        ).mappings().all()
        stage_start = profile["planting_date"]
        for stage in stages:
            stage_end = stage_start + timedelta(days=stage["duration_days"] - 1)
            if stage_start <= as_of <= stage_end:
                lower = float(stage["moisture_min"]) if stage["moisture_min"] is not None else fallback_threshold
                upper = float(stage["moisture_max"]) if stage["moisture_max"] is not None else None
                return {
                    "lower": lower,
                    "upper": upper,
                    "source": "production_stage",
                    "stageCode": stage["stage_code"],
                    "stageName": stage["stage_name"],
                }
            stage_start = stage_end + timedelta(days=1)
    return {
        "lower": fallback_threshold,
        "upper": None,
        "source": "plot_threshold",
        "stageCode": None,
        "stageName": None,
    }


def affected_task_titles(connection: Any, *, plot_id: int, as_of: date) -> list[str]:
    rows = connection.execute(
        text(
            "SELECT t.title FROM management_task t "
            "JOIN management_plan p ON p.plan_id = t.plan_id "
            "WHERE t.plot_id = :plot AND p.plan_status = 'active' "
            "AND t.task_status IN ('pending', 'in_progress') "
            "AND t.scheduled_date >= :start AND t.scheduled_date <= :end "
            "ORDER BY t.scheduled_date, t.task_id LIMIT 3"
        ),
        {"plot": plot_id, "start": as_of, "end": as_of + timedelta(days=7)},
    ).scalars().all()
    return [str(title) for title in rows]


def moisture_alert_description(
    *,
    moisture: float,
    threshold: float,
    direction: str,
    rule: dict[str, Any],
    tasks: list[str],
) -> str:
    comparison = "低于" if direction == "low" else "高于"
    bound = "下限" if direction == "low" else "上限"
    if rule["source"] == "production_stage":
        basis = f"{rule['stageName']}墒情目标{bound} {threshold:g}%"
    else:
        basis = f"地块基础阈值 {threshold:g}%"
    task_text = f"；未来7天关联任务：{'、'.join(tasks)}" if tasks else "；未来7天暂无关联计划任务"
    return f"当前土壤湿度 {moisture:g}% {comparison}{basis}{task_text}"


def _open_alert(
    connection: Any,
    *,
    plot_id: int,
    device_id: int | None,
    alert_type: str,
    description: str,
    moisture: float,
    threshold: float,
    timestamp: datetime,
) -> None:
    existing = connection.execute(
        text(
            "SELECT alert_id FROM alert WHERE plot_id = :plot AND device_id <=> :device "
            "AND alert_type = :type AND alert_status IN ('active', 'acknowledged') LIMIT 1"
        ),
        {"plot": plot_id, "device": device_id, "type": alert_type},
    ).scalar()
    if existing is None:
        connection.execute(
            text(
                "INSERT INTO alert (plot_id, device_id, alert_type, alert_description, "
                "alert_value, alert_threshold, alert_datetime, alert_status) "
                "VALUES (:plot, :device, :type, :description, :value, :threshold, :timestamp, 'active')"
            ),
            {
                "plot": plot_id,
                "device": device_id,
                "type": alert_type,
                "description": description,
                "value": moisture,
                "threshold": threshold,
                "timestamp": timestamp,
            },
        )


def _recover_alert(
    connection: Any,
    *,
    plot_id: int,
    alert_type: str,
    timestamp: datetime,
) -> None:
    connection.execute(
        text(
            "UPDATE alert SET alert_status = 'recovered', handled_at = :timestamp "
            "WHERE plot_id = :plot AND alert_type = :type "
            "AND alert_status IN ('active', 'acknowledged')"
        ),
        {"plot": plot_id, "type": alert_type, "timestamp": timestamp},
    )


def evaluate_moisture_alerts(
    connection: Any,
    *,
    plot_id: int,
    device_id: int | None,
    moisture: float,
    fallback_threshold: float | None,
    timestamp: datetime,
) -> dict[str, Any]:
    """Open or recover stage-aware moisture alerts and return the applied rule."""
    rule = current_moisture_rule(
        connection,
        plot_id=plot_id,
        fallback_threshold=fallback_threshold,
        as_of=timestamp.date(),
    )
    tasks = affected_task_titles(connection, plot_id=plot_id, as_of=timestamp.date())
    lower = rule["lower"]
    upper = rule["upper"]

    if lower is not None and moisture < lower:
        _open_alert(
            connection,
            plot_id=plot_id,
            device_id=device_id,
            alert_type="low_moisture",
            description=moisture_alert_description(
                moisture=moisture, threshold=lower, direction="low", rule=rule, tasks=tasks
            ),
            moisture=moisture,
            threshold=lower,
            timestamp=timestamp,
        )
    else:
        _recover_alert(connection, plot_id=plot_id, alert_type="low_moisture", timestamp=timestamp)

    sync_low_moisture_reminder(
        connection,
        plot_id=plot_id,
        moisture=moisture,
        lower_bound=lower,
        stage_name=rule["stageName"],
        timestamp=timestamp,
    )

    if upper is not None and moisture > upper:
        _open_alert(
            connection,
            plot_id=plot_id,
            device_id=device_id,
            alert_type="high_moisture",
            description=moisture_alert_description(
                moisture=moisture, threshold=upper, direction="high", rule=rule, tasks=tasks
            ),
            moisture=moisture,
            threshold=upper,
            timestamp=timestamp,
        )
    else:
        _recover_alert(connection, plot_id=plot_id, alert_type="high_moisture", timestamp=timestamp)

    return rule
