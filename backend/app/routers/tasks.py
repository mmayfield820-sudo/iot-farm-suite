from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..access import parse_resource_id, require_plot_access
from ..auth import current_user
from ..db import engine, utc_isoformat, utc_naive
from ..services.audit_service import write_audit_log


router = APIRouter(prefix="/api", tags=["tasks"])


class TaskUpdateRequest(BaseModel):
    plannedDate: date | None = None
    taskNote: str | None = Field(default=None, max_length=255)
    taskStatus: str | None = None


class TaskCompleteRequest(BaseModel):
    completedAt: datetime
    completionNote: str | None = Field(default=None, max_length=255)
    irrigationRecordId: str | None = None


class TemporaryTaskRequest(BaseModel):
    plotId: str
    taskType: str = Field(min_length=1, max_length=50)
    taskName: str = Field(min_length=1, max_length=100)
    plannedDate: date | None = None
    taskNote: str | None = Field(default=None, max_length=255)


def _today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def _payload(row: Any) -> dict[str, Any]:
    return {
        "taskId": f"TASK{row['task_id']:03d}",
        "plotId": f"P{row['plot_id']:03d}",
        "templateId": f"T{row['template_id']:03d}" if row["template_id"] else None,
        "planBatchNo": row["plan_batch_no"],
        "stageCode": row["stage_code"],
        "taskType": row["task_type"],
        "taskName": row["task_name"],
        "taskSource": row["task_source"],
        "plannedDate": row["planned_date"].isoformat() if row["planned_date"] else None,
        "taskStatus": row["task_status"],
        "taskNote": row["task_note"],
        "completedAt": utc_isoformat(row["completed_at"]),
        "completedBy": f"U{row['completed_by']:03d}" if row["completed_by"] else None,
        "completionNote": row["completion_note"],
        "irrigationRecordId": str(row["irrigation_record_id"]) if row["irrigation_record_id"] else None,
        "createdAt": utc_isoformat(row["created_at"]),
        "updatedAt": utc_isoformat(row["updated_at"]),
    }


def _accessible(rows: list[Any], user: dict[str, Any]) -> list[dict[str, Any]]:
    allowed: set[int] = set()
    denied: set[int] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        plot_id = row["plot_id"]
        if plot_id not in allowed and plot_id not in denied:
            try:
                require_plot_access(plot_id, user)
                allowed.add(plot_id)
            except HTTPException as error:
                if error.status_code == 403:
                    denied.add(plot_id)
                else:
                    raise
        if plot_id in allowed:
            result.append(_payload(row))
    return result


def _query_tasks(where: str, params: dict[str, Any], user: dict[str, Any]) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(f"SELECT * FROM farm_task WHERE {where} ORDER BY planned_date, task_id"),
            params,
        ).mappings().all()
    return _accessible(list(rows), user)


@router.get("/tasks/today")
def today_tasks(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return _query_tasks("planned_date=:today AND task_status IN ('PENDING','OVERDUE')", {"today": _today()}, user)


@router.get("/tasks/upcoming")
def upcoming_tasks(
    days: int = Query(default=7, ge=1, le=90),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    today = _today()
    return _query_tasks(
        "planned_date>:today AND planned_date<=:end_date AND task_status IN ('PENDING','OVERDUE')",
        {"today": today, "end_date": today + timedelta(days=days)},
        user,
    )


@router.get("/tasks/calendar")
def calendar_tasks(
    month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    plotId: str | None = None,
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    start = date.fromisoformat(f"{month}-01")
    end = date(start.year + (1 if start.month == 12 else 0), 1 if start.month == 12 else start.month + 1, 1)
    where = "planned_date>=:start AND planned_date<:end"
    params: dict[str, Any] = {"start": start, "end": end}
    if plotId:
        numeric_plot_id = parse_resource_id(plotId, "P")
        require_plot_access(numeric_plot_id, user)
        where += " AND plot_id=:plot_id"
        params["plot_id"] = numeric_plot_id
    return _query_tasks(where, params, user)


@router.get("/plots/{plot_id}/tasks")
def plot_tasks(plot_id: str, user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    numeric_id = parse_resource_id(plot_id, "P")
    require_plot_access(numeric_id, user)
    return _query_tasks("plot_id=:plot_id", {"plot_id": numeric_id}, user)


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_id = parse_resource_id(task_id, "TASK")
    fields = request.model_fields_set
    if not fields:
        raise HTTPException(status_code=400, detail="NO_TASK_FIELDS_TO_UPDATE")
    if request.taskStatus is not None and request.taskStatus not in {"PENDING", "CANCELLED"}:
        raise HTTPException(status_code=400, detail="TASK_STATUS_NOT_EDITABLE")
    with engine.begin() as connection:
        existing = connection.execute(
            text("SELECT * FROM farm_task WHERE task_id=:task_id FOR UPDATE"),
            {"task_id": numeric_id},
        ).mappings().first()
        if existing is None:
            raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
        require_plot_access(existing["plot_id"], user)
        if existing["task_status"] in {"COMPLETED", "SUPERSEDED"}:
            raise HTTPException(status_code=409, detail="TASK_NOT_EDITABLE")
        updates: list[str] = []
        params: dict[str, Any] = {"task_id": numeric_id}
        mapping = {"plannedDate": ("planned_date", request.plannedDate), "taskNote": ("task_note", request.taskNote), "taskStatus": ("task_status", request.taskStatus)}
        for field in fields:
            column, value = mapping[field]
            updates.append(f"{column}=:{column}")
            params[column] = value.strip() if isinstance(value, str) else value
        connection.execute(text(f"UPDATE farm_task SET {', '.join(updates)}, updated_at=UTC_TIMESTAMP(6) WHERE task_id=:task_id"), params)
        updated = connection.execute(text("SELECT * FROM farm_task WHERE task_id=:task_id"), {"task_id": numeric_id}).mappings().one()
        write_audit_log(connection, user=user, action_type="UPDATE", resource_type="FARM_TASK", resource_id=f"TASK{numeric_id:03d}", description="调整农事任务", before_data=_payload(existing), after_data=_payload(updated))
    return _payload(updated)


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    request: TaskCompleteRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_id = parse_resource_id(task_id, "TASK")
    try:
        completed_at = utc_naive(request.completedAt)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    irrigation_id = parse_resource_id(request.irrigationRecordId, "IR") if request.irrigationRecordId else None
    with engine.begin() as connection:
        existing = connection.execute(text("SELECT * FROM farm_task WHERE task_id=:task_id FOR UPDATE"), {"task_id": numeric_id}).mappings().first()
        if existing is None:
            raise HTTPException(status_code=404, detail="TASK_NOT_FOUND")
        require_plot_access(existing["plot_id"], user)
        if existing["task_status"] in {"COMPLETED", "SUPERSEDED", "CANCELLED"}:
            raise HTTPException(status_code=409, detail="TASK_CANNOT_BE_COMPLETED")
        if irrigation_id is not None:
            record_plot = connection.execute(text("SELECT plot_id FROM irrigation_record WHERE record_id=:record_id"), {"record_id": irrigation_id}).scalar()
            if record_plot is None or record_plot != existing["plot_id"]:
                raise HTTPException(status_code=400, detail="IRRIGATION_RECORD_NOT_FOR_TASK_PLOT")
        connection.execute(
            text("UPDATE farm_task SET task_status='COMPLETED', completed_at=:completed_at, completed_by=:user_id, completion_note=:note, irrigation_record_id=:irrigation_id, updated_at=UTC_TIMESTAMP(6) WHERE task_id=:task_id"),
            {"completed_at": completed_at, "user_id": user["user_id"], "note": request.completionNote.strip() if request.completionNote else None, "irrigation_id": irrigation_id, "task_id": numeric_id},
        )
        updated = connection.execute(text("SELECT * FROM farm_task WHERE task_id=:task_id"), {"task_id": numeric_id}).mappings().one()
        write_audit_log(connection, user=user, action_type="COMPLETE", resource_type="FARM_TASK", resource_id=f"TASK{numeric_id:03d}", description="完成农事任务", before_data=_payload(existing), after_data=_payload(updated))
    return _payload(updated)


@router.post("/farm-tasks/temporary", status_code=201)
def create_temporary_task(
    request: TemporaryTaskRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    plot_id = parse_resource_id(request.plotId, "P")
    require_plot_access(plot_id, user)
    with engine.begin() as connection:
        result = connection.execute(
            text("INSERT INTO farm_task (plot_id,task_type,task_name,task_source,planned_date,task_status,task_note,created_at,updated_at) VALUES (:plot_id,:task_type,:task_name,'TEMPORARY',:planned_date,'PENDING',:task_note,UTC_TIMESTAMP(6),UTC_TIMESTAMP(6))"),
            {"plot_id": plot_id, "task_type": request.taskType.strip(), "task_name": request.taskName.strip(), "planned_date": request.plannedDate or _today(), "task_note": request.taskNote.strip() if request.taskNote else None},
        )
        task_id = result.lastrowid
        row = connection.execute(text("SELECT * FROM farm_task WHERE task_id=:task_id"), {"task_id": task_id}).mappings().one()
        write_audit_log(connection, user=user, action_type="CREATE", resource_type="FARM_TASK", resource_id=f"TASK{task_id:03d}", description="新增临时农事任务", after_data=_payload(row))
    return _payload(row)
