from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..access import accessible_farm_ids, parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine
from ..services.audit_service import write_audit_log
from ..services.plan_change_service import json_value, request_payload


router = APIRouter(prefix="/api/plan-change-requests", tags=["plan-change-requests"])


class ReviewRequest(BaseModel):
    reviewComment: str | None = Field(default=None, max_length=255)


def _load(connection: Any, request_id: int, *, for_update: bool = False) -> Any:
    suffix = " FOR UPDATE" if for_update else ""
    return connection.execute(text("""
        SELECT r.*, p.plot_name, p.farm_id, f.farm_name,
               COALESCE(requester.real_name, requester.username) requester_name,
               COALESCE(reviewer.real_name, reviewer.username) reviewer_name
        FROM plan_change_request r
        JOIN plot p ON p.plot_id=r.plot_id JOIN farm f ON f.farm_id=p.farm_id
        JOIN users requester ON requester.user_id=r.requested_by
        LEFT JOIN users reviewer ON reviewer.user_id=r.reviewed_by
        WHERE r.request_id=:request_id
    """ + suffix), {"request_id": request_id}).mappings().first()


@router.get("")
def list_requests(plotId: str | None = None, status: str | None = None, user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    clauses = []
    if plotId:
        numeric_plot = parse_resource_id(plotId, "P")
        require_plot_access(numeric_plot, user)
        clauses.append("r.plot_id=:plot_id")
        params["plot_id"] = numeric_plot
    if status:
        clauses.append("r.request_status=:status")
        params["status"] = status
    if user["role"] == "farmer":
        clauses.append("r.requested_by=:user_id")
        params["user_id"] = user["user_id"]
    elif user["role"] == "farm_admin":
        farm_ids = sorted(accessible_farm_ids(user) or [])
        if not farm_ids:
            return []
        placeholders = []
        for index, farm_id in enumerate(farm_ids):
            key = f"farm_{index}"
            params[key] = farm_id
            placeholders.append(f":{key}")
        clauses.append(f"p.farm_id IN ({','.join(placeholders)})")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with engine.connect() as connection:
        rows = connection.execute(text("""
            SELECT r.*, p.plot_name, p.farm_id, f.farm_name,
                   COALESCE(requester.real_name, requester.username) requester_name,
                   COALESCE(reviewer.real_name, reviewer.username) reviewer_name
            FROM plan_change_request r
            JOIN plot p ON p.plot_id=r.plot_id JOIN farm f ON f.farm_id=p.farm_id
            JOIN users requester ON requester.user_id=r.requested_by
            LEFT JOIN users reviewer ON reviewer.user_id=r.reviewed_by
        """ + where + " ORDER BY r.created_at DESC"), params).mappings().all()
    return [request_payload(row) for row in rows]


def _require_admin(user: dict[str, Any]) -> None:
    if user["role"] != "farm_admin":
        raise HTTPException(status_code=403, detail="FARM_ADMIN_REQUIRED")


@router.post("/{request_id}/approve")
def approve_request(request_id: str, request: ReviewRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    _require_admin(user)
    numeric_id = parse_resource_id(request_id, "PCR")
    with engine.begin() as connection:
        row = _load(connection, numeric_id, for_update=True)
        if row is None:
            raise HTTPException(status_code=404, detail="PLAN_CHANGE_REQUEST_NOT_FOUND")
        require_plot_access(int(row["plot_id"]), user)
        if row["request_status"] != "PENDING_REVIEW":
            raise HTTPException(status_code=409, detail="PLAN_CHANGE_REQUEST_NOT_PENDING")
        connection.execute(text("""
            UPDATE plan_change_request SET request_status='APPROVED', reviewed_by=:user_id,
              reviewed_at=UTC_TIMESTAMP(6), review_comment=:comment, updated_at=UTC_TIMESTAMP(6)
            WHERE request_id=:request_id
        """), {"user_id": user["user_id"], "comment": request.reviewComment, "request_id": numeric_id})
        write_audit_log(connection, user=user, action_type="APPROVE", resource_type="PLAN_CHANGE_REQUEST",
                        resource_id=row["request_no"], description="确认农户生成的新管理计划",
                        before_data={"status": "PENDING_REVIEW"}, after_data={"status": "APPROVED", "comment": request.reviewComment})
        updated = _load(connection, numeric_id)
    return request_payload(updated)


@router.post("/{request_id}/rollback")
def rollback_request(request_id: str, request: ReviewRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    _require_admin(user)
    comment = (request.reviewComment or "").strip()
    if not comment:
        raise HTTPException(status_code=400, detail="REVIEW_COMMENT_REQUIRED")
    numeric_id = parse_resource_id(request_id, "PCR")
    with engine.begin() as connection:
        row = _load(connection, numeric_id, for_update=True)
        if row is None:
            raise HTTPException(status_code=404, detail="PLAN_CHANGE_REQUEST_NOT_FOUND")
        require_plot_access(int(row["plot_id"]), user)
        if row["request_status"] != "PENDING_REVIEW":
            raise HTTPException(status_code=409, detail="PLAN_CHANGE_REQUEST_NOT_PENDING")
        before = json_value(row["before_snapshot"]) or {}
        planting = before.get("planting") or {}
        stage_by = planting.get("stageOverrideBy")
        stage_by_id = int(stage_by[1:]) if isinstance(stage_by, str) and stage_by.startswith("U") else None
        stage_at = planting.get("stageOverrideAt")
        if stage_at:
            stage_at = datetime.fromisoformat(stage_at.replace("Z", "+00:00")).replace(tzinfo=None)
        template_id = planting.get("templateId")
        template_id = int(template_id[1:]) if isinstance(template_id, str) and template_id.startswith("T") else None
        connection.execute(text("""
            UPDATE plot SET template_id=:template_id,
              planting_date=:planting_date,
              soil_type=:soil_type,
              planting_remark=:planting_remark,
              stage_override_code=:code, stage_override_reason=:reason,
              stage_override_by=:stage_by, stage_override_at=:stage_at WHERE plot_id=:plot_id
        """), {"template_id": template_id, "planting_date": planting.get("plantingDate"),
                  "soil_type": planting.get("soilType"), "planting_remark": planting.get("plantingRemark"),
                  "code": planting.get("stageOverrideCode"), "reason": planting.get("stageOverrideReason"),
                  "stage_by": stage_by_id, "stage_at": stage_at, "plot_id": row["plot_id"]})
        if row["proposed_plan_batch_no"]:
            connection.execute(text("UPDATE farm_task SET task_status='SUPERSEDED' WHERE plot_id=:plot_id AND plan_batch_no=:batch AND task_status IN ('PENDING','OVERDUE')"),
                               {"plot_id": row["plot_id"], "batch": row["proposed_plan_batch_no"]})
        for task in (before.get("plan") or {}).get("tasks", []):
            connection.execute(text("UPDATE farm_task SET task_status=:status, updated_at=UTC_TIMESTAMP(6) WHERE task_id=:task_id"),
                               {"status": task["task_status"], "task_id": task["task_id"]})
        connection.execute(text("""
            UPDATE plan_change_request SET request_status='ROLLED_BACK', reviewed_by=:user_id,
              reviewed_at=UTC_TIMESTAMP(6), review_comment=:comment, rolled_back_at=UTC_TIMESTAMP(6),
              updated_at=UTC_TIMESTAMP(6) WHERE request_id=:request_id
        """), {"user_id": user["user_id"], "comment": comment, "request_id": numeric_id})
        write_audit_log(connection, user=user, action_type="ROLLBACK", resource_type="PLAN_CHANGE_REQUEST",
                        resource_id=row["request_no"], description="退回农户计划变更并恢复原状态",
                        before_data={"status": "PENDING_REVIEW", "proposedPlanBatchNo": row["proposed_plan_batch_no"]},
                        after_data={"status": "ROLLED_BACK", "comment": comment, "restoredPlanBatchNo": row["original_plan_batch_no"]})
        updated = _load(connection, numeric_id)
    return request_payload(updated)
