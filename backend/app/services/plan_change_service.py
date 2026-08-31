from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text


def json_value(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def create_draft_request(
    connection: Any,
    *,
    plot_id: int,
    user: dict[str, Any],
    request_type: str,
    reason: str,
    before_snapshot: dict[str, Any],
    after_snapshot: dict[str, Any],
    original_stage_code: str | None,
    proposed_stage_code: str | None,
) -> int:
    pending = connection.execute(
        text("SELECT request_id FROM plan_change_request WHERE plot_id=:plot_id AND request_status='PENDING_REVIEW' LIMIT 1"),
        {"plot_id": plot_id},
    ).scalar()
    if pending:
        raise HTTPException(status_code=409, detail="PLAN_CHANGE_REVIEW_PENDING")
    connection.execute(
        text("UPDATE plan_change_request SET request_status='CANCELLED' WHERE plot_id=:plot_id AND requested_by=:user_id AND request_status='DRAFT'"),
        {"plot_id": plot_id, "user_id": user["user_id"]},
    )
    result = connection.execute(
        text(
            """
            INSERT INTO plan_change_request (
              request_no, plot_id, request_type, request_source, requested_by,
              request_reason, original_stage_code, proposed_stage_code,
              before_snapshot, after_snapshot, request_status
            ) VALUES (
              REPLACE(UUID(), '-', ''), :plot_id, :request_type, 'FARMER_MANUAL', :requested_by,
              :reason, :original_stage_code, :proposed_stage_code,
              :before_snapshot, :after_snapshot, 'DRAFT'
            )
            """
        ),
        {
            "plot_id": plot_id,
            "request_type": request_type,
            "requested_by": user["user_id"],
            "reason": reason,
            "original_stage_code": original_stage_code,
            "proposed_stage_code": proposed_stage_code,
            "before_snapshot": json.dumps(before_snapshot, ensure_ascii=False, default=str),
            "after_snapshot": json.dumps(after_snapshot, ensure_ascii=False, default=str),
        },
    )
    request_id = int(result.lastrowid)
    connection.execute(
        text("UPDATE plan_change_request SET request_no=:request_no WHERE request_id=:request_id"),
        {"request_no": f"PCR{request_id:06d}", "request_id": request_id},
    )
    return request_id


def request_payload(row: Any) -> dict[str, Any]:
    return {
        "requestId": f"PCR{int(row['request_id']):06d}",
        "requestNo": row["request_no"],
        "plotId": f"P{int(row['plot_id']):03d}",
        "plotName": row["plot_name"],
        "farmId": f"F{int(row['farm_id']):03d}",
        "farmName": row["farm_name"],
        "requestType": row["request_type"],
        "requestSource": row["request_source"],
        "requestedBy": row["requester_name"],
        "requestReason": row["request_reason"],
        "originalStageCode": row["original_stage_code"],
        "proposedStageCode": row["proposed_stage_code"],
        "originalPlanBatchNo": row["original_plan_batch_no"],
        "proposedPlanBatchNo": row["proposed_plan_batch_no"],
        "beforeSnapshot": json_value(row["before_snapshot"]),
        "afterSnapshot": json_value(row["after_snapshot"]),
        "status": row["request_status"],
        "submittedAt": row["submitted_at"].isoformat() + "Z" if row["submitted_at"] else None,
        "reviewedBy": row["reviewer_name"],
        "reviewedAt": row["reviewed_at"].isoformat() + "Z" if row["reviewed_at"] else None,
        "reviewComment": row["review_comment"],
        "createdAt": row["created_at"].isoformat() + "Z" if row["created_at"] else None,
    }
