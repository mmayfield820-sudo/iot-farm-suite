from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..access import parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine
from ..services.audit_service import write_audit_log
from ..services.plan_change_service import json_value
from ..services.plan_service import preview_plan
from ..services.stage_service import resolve_stage


router = APIRouter(prefix="/api/plots", tags=["plans"])


class PlanTaskRequest(BaseModel):
    plannedDate: date
    stageCode: str = Field(min_length=1, max_length=50)
    taskType: str = Field(min_length=1, max_length=50)
    taskName: str = Field(min_length=1, max_length=100)


class PlanGenerateRequest(BaseModel):
    regenerate: bool = False
    tasks: list[PlanTaskRequest] | None = None


def _today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def _load_context(connection: Any, plot_id: int) -> Any:
    return connection.execute(
        text(
            """
            SELECT p.plot_id, p.plot_code, p.plot_name, p.template_id, p.planting_date,
                   p.stage_override_code, t.template_code, t.template_name, t.version,
                   t.template_content
            FROM plot AS p
            JOIN cultivation_template AS t ON t.template_id=p.template_id
            WHERE p.plot_id=:plot_id
            """
        ),
        {"plot_id": plot_id},
    ).mappings().first()


def _plan_preview(plot_id: int) -> dict[str, Any]:
    with engine.connect() as connection:
        context = _load_context(connection, plot_id)
        if context is None or context["planting_date"] is None:
            raise HTTPException(status_code=409, detail="PLOT_PLANTING_NOT_CONFIGURED")
        active_count = connection.execute(
            text("SELECT COUNT(*) FROM farm_task WHERE plot_id=:plot_id AND task_status IN ('PENDING','OVERDUE')"),
            {"plot_id": plot_id},
        ).scalar_one()
        completed_count = connection.execute(
            text("SELECT COUNT(*) FROM farm_task WHERE plot_id=:plot_id AND task_status='COMPLETED'"),
            {"plot_id": plot_id},
        ).scalar_one()
    content = context["template_content"]
    if isinstance(content, str):
        content = json.loads(content)
    today = _today()
    current_stage = resolve_stage(
        content,
        today=today,
        planting_date=context["planting_date"],
        override_code=context["stage_override_code"],
    )
    try:
        tasks = preview_plan(content, today=today, override_code=context["stage_override_code"])
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "plotId": f"P{plot_id:03d}",
        "plotName": context["plot_name"],
        "templateId": f"T{context['template_id']:03d}",
        "templateCode": context["template_code"],
        "templateName": context["template_name"],
        "templateVersion": context["version"],
        "currentStage": current_stage,
        "tasks": tasks,
        "summary": {"oldPendingTasks": active_count, "newPlanTasks": len(tasks), "completedTasksKept": completed_count},
    }


@router.post("/{plot_id}/plans/preview")
def preview_plot_plan(plot_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    return _plan_preview(numeric_id)


@router.post("/{plot_id}/plans/generate", status_code=201)
def generate_plot_plan(
    plot_id: str,
    request: PlanGenerateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    preview = _plan_preview(numeric_id)
    if request.tasks is not None:
        with engine.connect() as connection:
            validation_context = _load_context(connection, numeric_id)
        content = validation_context["template_content"]
        if isinstance(content, str):
            content = json.loads(content)
        stage_names = {stage["code"]: stage["name"] for stage in content.get("stages", [])}
        invalid_stages = [task.stageCode for task in request.tasks if task.stageCode not in stage_names]
        if invalid_stages:
            raise HTTPException(status_code=400, detail="PLAN_TASK_STAGE_NOT_IN_TEMPLATE")
        preview["tasks"] = [
            {
                "plannedDate": task.plannedDate.isoformat(),
                "stageCode": task.stageCode,
                "stageName": stage_names[task.stageCode],
                "taskType": task.taskType.strip(),
                "taskName": task.taskName.strip(),
                "taskSource": "PLAN",
            }
            for task in request.tasks
        ]
        preview["summary"]["newPlanTasks"] = len(preview["tasks"])
    if not preview["tasks"]:
        raise HTTPException(status_code=409, detail="PLAN_HAS_NO_TASKS")
    today = _today()
    with engine.begin() as connection:
        context = _load_context(connection, numeric_id)
        active_rows = connection.execute(
            text("SELECT task_id, plan_batch_no, task_status, planned_date, stage_code, task_type, task_name FROM farm_task WHERE plot_id=:plot_id AND task_status IN ('PENDING','OVERDUE') FOR UPDATE"),
            {"plot_id": numeric_id},
        ).mappings().all()
        draft = connection.execute(
            text("SELECT * FROM plan_change_request WHERE plot_id=:plot_id AND requested_by=:user_id AND request_status='DRAFT' ORDER BY request_id DESC LIMIT 1 FOR UPDATE"),
            {"plot_id": numeric_id, "user_id": user["user_id"]},
        ).mappings().first()
        if active_rows and not request.regenerate:
            raise HTTPException(status_code=409, detail="PLAN_ALREADY_EXISTS_USE_REGENERATE")
        if request.regenerate:
            connection.execute(
                text("UPDATE farm_task SET task_status='SUPERSEDED', updated_at=UTC_TIMESTAMP(6) WHERE plot_id=:plot_id AND task_status IN ('PENDING','OVERDUE')"),
                {"plot_id": numeric_id},
            )
        sequence = connection.execute(
            text("SELECT COUNT(DISTINCT plan_batch_no)+1 FROM farm_task WHERE plot_id=:plot_id AND plan_batch_no LIKE :prefix"),
            {"plot_id": numeric_id, "prefix": f"PLAN-{context['plot_code'] or f'P{numeric_id:03d}'}-{today.strftime('%Y%m%d')}-%"},
        ).scalar_one()
        batch = f"PLAN-{context['plot_code'] or f'P{numeric_id:03d}'}-{today.strftime('%Y%m%d')}-{sequence:03d}"
        new_task_ids = []
        for task in preview["tasks"]:
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO farm_task (
                      plot_id, template_id, plan_batch_no, stage_code, task_type,
                      task_name, task_source, planned_date, task_status, created_at, updated_at
                    ) VALUES (
                      :plot_id, :template_id, :batch, :stage_code, :task_type,
                      :task_name, 'PLAN', :planned_date, 'PENDING', UTC_TIMESTAMP(6), UTC_TIMESTAMP(6)
                    )
                    """
                ),
                {
                    "plot_id": numeric_id,
                    "template_id": context["template_id"],
                    "batch": batch,
                    "stage_code": task["stageCode"],
                    "task_type": task["taskType"],
                    "task_name": task["taskName"],
                    "planned_date": task["plannedDate"],
                },
            )
            new_task_ids.append(int(inserted.lastrowid))
        if draft is not None:
            before_snapshot = json_value(draft["before_snapshot"]) or {}
            after_snapshot = json_value(draft["after_snapshot"]) or {}
            before_snapshot["plan"] = {"tasks": [dict(row) for row in active_rows]}
            after_snapshot["plan"] = {"planBatchNo": batch, "taskIds": new_task_ids, "tasks": preview["tasks"]}
            original_batch = next((row["plan_batch_no"] for row in active_rows if row["plan_batch_no"]), None)
            connection.execute(
                text(
                    """
                    UPDATE plan_change_request
                    SET original_plan_batch_no=:original_batch, proposed_plan_batch_no=:proposed_batch,
                        before_snapshot=:before_snapshot, after_snapshot=:after_snapshot,
                        request_status='PENDING_REVIEW', submitted_at=UTC_TIMESTAMP(6),
                        applied_at=UTC_TIMESTAMP(6), updated_at=UTC_TIMESTAMP(6)
                    WHERE request_id=:request_id
                    """
                ),
                {
                    "original_batch": original_batch,
                    "proposed_batch": batch,
                    "before_snapshot": json.dumps(before_snapshot, ensure_ascii=False, default=str),
                    "after_snapshot": json.dumps(after_snapshot, ensure_ascii=False, default=str),
                    "request_id": draft["request_id"],
                },
            )
            write_audit_log(
                connection, user=user, action_type="GENERATE_AND_SUBMIT",
                resource_type="PLAN_CHANGE_REQUEST", resource_id=draft["request_no"],
                description="生成新管理计划并提交管理员确认",
                before_data=before_snapshot, after_data={**after_snapshot, "status": "PENDING_REVIEW"},
            )
        else:
            write_audit_log(
                connection,
                user=user,
                action_type="REGENERATE" if request.regenerate else "GENERATE",
                resource_type="MANAGEMENT_PLAN",
                resource_id=batch,
                description="重新生成地块管理计划" if request.regenerate else "生成地块管理计划",
                before_data={"supersededTaskIds": [row["task_id"] for row in active_rows]},
                after_data={"plotId": f"P{numeric_id:03d}", "planBatchNo": batch, "taskCount": len(preview["tasks"])},
            )
    return {**preview, "planBatchNo": batch, "generatedAt": datetime.now(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")}
