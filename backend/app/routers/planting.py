from __future__ import annotations

import json
from datetime import date
from typing import Any
from zoneinfo import ZoneInfo
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..access import parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine, utc_isoformat
from ..services.audit_service import write_audit_log
from ..services.plan_change_service import create_draft_request
from ..services.stage_service import resolve_stage, validate_template_content


router = APIRouter(prefix="/api/plots", tags=["planting"])


class PlantingRequest(BaseModel):
    templateId: str
    plantingDate: date
    soilType: str | None = Field(default=None, max_length=50)
    plantingRemark: str | None = Field(default=None, max_length=255)


class StageOverrideRequest(BaseModel):
    stageCode: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1, max_length=255)


def _today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def _row_payload(row: Any) -> dict[str, Any]:
    template_content = row["template_content"]
    if isinstance(template_content, str):
        template_content = json.loads(template_content)
    current = resolve_stage(
        template_content,
        today=_today(),
        planting_date=row["planting_date"],
        override_code=row["stage_override_code"],
    )
    return {
        "plotId": f"P{row['plot_id']:03d}",
        "plotCode": row["plot_code"],
        "plotName": row["plot_name"],
        "templateId": f"T{row['template_id']:03d}",
        "templateCode": row["template_code"],
        "templateName": row["template_name"],
        "templateVersion": row["version"],
        "varietyName": row["variety_name"],
        "plantingDate": row["planting_date"].isoformat() if row["planting_date"] else None,
        "soilType": row["soil_type"],
        "plantingRemark": row["planting_remark"],
        "stageOverrideCode": row["stage_override_code"],
        "stageOverrideReason": row["stage_override_reason"],
        "stageOverrideBy": f"U{row['stage_override_by']:03d}" if row["stage_override_by"] else None,
        "stageOverrideAt": utc_isoformat(row["stage_override_at"]),
        "currentStage": current,
    }


def _load_planting(connection: Any, plot_id: int, *, for_update: bool = False) -> Any:
    suffix = " FOR UPDATE" if for_update else ""
    return connection.execute(
        text(
            """
            SELECT p.plot_id, p.plot_code, p.plot_name, p.template_id, p.planting_date,
                   p.soil_type, p.planting_remark, p.stage_override_code,
                   p.stage_override_reason, p.stage_override_by, p.stage_override_at,
                   t.template_code, t.template_name, t.variety_name, t.version,
                   t.template_content, t.template_status
            FROM plot AS p
            JOIN cultivation_template AS t ON t.template_id = p.template_id
            WHERE p.plot_id = :plot_id
            """ + suffix
        ),
        {"plot_id": plot_id},
    ).mappings().first()


@router.get("/{plot_id}/planting")
def get_planting(plot_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    with engine.connect() as connection:
        row = _load_planting(connection, numeric_id)
    if row is None:
        raise HTTPException(status_code=409, detail="PLOT_PLANTING_NOT_CONFIGURED")
    return _row_payload(row)


@router.put("/{plot_id}/planting")
def update_planting(
    plot_id: str,
    request: PlantingRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    template_id = parse_resource_id(request.templateId, "T")
    with engine.begin() as connection:
        existing = _load_planting(connection, numeric_id, for_update=True)
        template = connection.execute(
            text("SELECT template_id, template_status FROM cultivation_template WHERE template_id=:template_id"),
            {"template_id": template_id},
        ).mappings().first()
        if template is None:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        if template["template_status"] != "ACTIVE":
            raise HTTPException(status_code=409, detail="TEMPLATE_NOT_ACTIVE")
        connection.execute(
            text(
                """
                UPDATE plot
                SET template_id=:template_id, planting_date=:planting_date,
                    soil_type=:soil_type, planting_remark=:planting_remark
                WHERE plot_id=:plot_id
                """
            ),
            {
                "template_id": template_id,
                "planting_date": request.plantingDate,
                "soil_type": request.soilType.strip() if request.soilType else None,
                "planting_remark": request.plantingRemark.strip() if request.plantingRemark else None,
                "plot_id": numeric_id,
            },
        )
        updated = _load_planting(connection, numeric_id)
        write_audit_log(
            connection,
            user=user,
            action_type="UPDATE",
            resource_type="PLOT_PLANTING",
            resource_id=f"P{numeric_id:03d}",
            description="修改地块种植信息",
            before_data=_row_payload(existing) if existing is not None else None,
            after_data=_row_payload(updated),
        )
        changed_plan_basis = bool(
            existing is None
            or existing["template_id"] != template_id
            or existing["planting_date"] != request.plantingDate
        )
        if changed_plan_basis:
            create_draft_request(
                connection,
                plot_id=numeric_id,
                user=user,
                request_type="PLANTING_CHANGE",
                reason=request.plantingRemark.strip() if request.plantingRemark else "修改品种模板或定植日期",
                before_snapshot={"planting": _row_payload(existing) if existing is not None else None},
                after_snapshot={"planting": _row_payload(updated)},
                original_stage_code=before.get("currentStage", {}).get("stageCode") if (before := (_row_payload(existing) if existing else {})) else None,
                proposed_stage_code=_row_payload(updated).get("currentStage", {}).get("stageCode"),
            )
    result = _row_payload(updated)
    result["regenerationRecommended"] = changed_plan_basis
    return result


@router.get("/{plot_id}/stage")
def get_current_stage(plot_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    planting = get_planting(plot_id, user)
    return {
        "plotId": planting["plotId"],
        **planting["currentStage"],
        "overrideCode": planting["stageOverrideCode"],
        "overrideReason": planting["stageOverrideReason"],
    }


@router.put("/{plot_id}/stage")
def override_stage(
    plot_id: str,
    request: StageOverrideRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    reason = request.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="STAGE_OVERRIDE_REASON_REQUIRED")
    with engine.begin() as connection:
        existing = _load_planting(connection, numeric_id, for_update=True)
        if existing is None:
            raise HTTPException(status_code=409, detail="PLOT_PLANTING_NOT_CONFIGURED")
        content = validate_template_content(existing["template_content"])
        if not any(stage["code"] == request.stageCode for stage in content["stages"]):
            raise HTTPException(status_code=400, detail="STAGE_NOT_IN_TEMPLATE")
        before = _row_payload(existing)
        connection.execute(
            text(
                """
                UPDATE plot
                SET stage_override_code=:stage_code, stage_override_reason=:reason,
                    stage_override_by=:user_id, stage_override_at=UTC_TIMESTAMP(6)
                WHERE plot_id=:plot_id
                """
            ),
            {
                "stage_code": request.stageCode,
                "reason": reason,
                "user_id": user["user_id"],
                "plot_id": numeric_id,
            },
        )
        updated = _load_planting(connection, numeric_id)
        after = _row_payload(updated)
        write_audit_log(
            connection,
            user=user,
            action_type="STAGE_OVERRIDE",
            resource_type="PLOT_STAGE",
            resource_id=f"P{numeric_id:03d}",
            description="人工修正地块当前生长阶段",
            before_data=before,
            after_data=after,
        )
        create_draft_request(
            connection,
            plot_id=numeric_id,
            user=user,
            request_type="STAGE_OVERRIDE",
            reason=reason,
            before_snapshot={"planting": before},
            after_snapshot={"planting": after},
            original_stage_code=before.get("currentStage", {}).get("stageCode"),
            proposed_stage_code=request.stageCode,
        )
    return {
        **after["currentStage"],
        "plotId": after["plotId"],
        "overrideReason": after["stageOverrideReason"],
        "regenerationRecommended": True,
        "message": "阶段已修正，建议重新生成管理计划",
    }
