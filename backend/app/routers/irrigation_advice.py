from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from ..access import parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine, utc_isoformat
from ..services.irrigation_advice_service import build_irrigation_advice
from ..services.stage_service import resolve_stage
from ..services.weather_service import weather_service


router = APIRouter(prefix="/api/plots", tags=["irrigation-advice"])


@router.get("/{plot_id}/irrigation-advice")
def irrigation_advice(plot_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    with engine.connect() as connection:
        context = connection.execute(
            text(
                """
                SELECT p.location, p.planting_date, p.stage_override_code,
                       f.city, f.address, t.template_content,
                       c.soil_moisture_threshold, c.irrigation_length
                FROM plot p
                JOIN farm f ON f.farm_id=p.farm_id
                LEFT JOIN cultivation_template t ON t.template_id=p.template_id
                LEFT JOIN threshold_config c ON c.plot_id=p.plot_id
                WHERE p.plot_id=:plot_id
                """
            ),
            {"plot_id": numeric_id},
        ).mappings().one()
        report = connection.execute(
            text("SELECT plot_moisture,report_datetime FROM plot_report WHERE plot_id=:plot_id ORDER BY report_datetime DESC LIMIT 1"),
            {"plot_id": numeric_id},
        ).mappings().first()
        device = connection.execute(
            text("SELECT status,last_heartbeat FROM device WHERE plot_id=:plot_id AND device_type='irrigation' LIMIT 1"),
            {"plot_id": numeric_id},
        ).mappings().first()
        irrigation = connection.execute(
            text("SELECT requested_at FROM irrigation_record WHERE plot_id=:plot_id AND status='success' ORDER BY requested_at DESC LIMIT 1"),
            {"plot_id": numeric_id},
        ).mappings().first()
    stage_code = None
    if context["template_content"]:
        content = json.loads(context["template_content"]) if isinstance(context["template_content"], str) else context["template_content"]
        stage_code = resolve_stage(content, today=datetime.now(ZoneInfo("Asia/Shanghai")).date(), planting_date=context["planting_date"], override_code=context["stage_override_code"])["stageCode"]
    stale_before = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=int(os.getenv("DEVICE_OFFLINE_TIMEOUT_SECONDS", "90")))
    device_online = bool(device and device["status"] == "online" and device["last_heartbeat"] and device["last_heartbeat"] >= stale_before)
    location = context["location"] or context["address"] or context["city"] or "重庆市奉节县"
    weather = weather_service.get_forecast(numeric_id, location)
    advice = build_irrigation_advice(
        current_moisture=float(report["plot_moisture"]) if report else None,
        threshold=float(context["soil_moisture_threshold"]) if context["soil_moisture_threshold"] is not None else None,
        suggested_duration=int(context["irrigation_length"] or 20),
        stage_code=stage_code,
        device_online=device_online,
        weather=weather,
        latest_irrigation_at=utc_isoformat(irrigation["requested_at"]) if irrigation else None,
    )
    return {
        "plotId": f"P{numeric_id:03d}",
        **advice,
    }
