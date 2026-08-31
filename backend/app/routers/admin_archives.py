from __future__ import annotations

from decimal import Decimal
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..access import accessible_farm_ids, parse_resource_id, require_system_admin
from ..auth import current_user
from ..db import engine, utc_isoformat
from ..services.audit_service import write_audit_log
from ..services.stage_service import resolve_stage


router = APIRouter(prefix="/api", tags=["admin-archives"])


class FarmArchiveRequest(BaseModel):
    farmName: str = Field(min_length=1, max_length=100)
    province: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    areaMu: Decimal | None = Field(default=None, ge=0)
    adminUserId: str | None = None
    remark: str | None = Field(default=None, max_length=255)
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class PlotArchiveRequest(BaseModel):
    farmId: str
    plotCode: str = Field(min_length=1, max_length=50)
    plotName: str = Field(min_length=1, max_length=100)
    areaMu: Decimal | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=255)
    irrigationMethod: str | None = Field(default=None, max_length=50)
    farmerUserId: str | None = None
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


def _farm_payload(row: Any) -> dict[str, Any]:
    return {"id": f"F{row['farm_id']:03d}", "farmName": row["farm_name"], "province": row["province"], "city": row["city"], "address": row["address"], "areaMu": float(row["area_mu"]) if row["area_mu"] is not None else None, "adminUserId": f"U{row['admin_user_id']:03d}" if row["admin_user_id"] else None, "status": row["farm_status"], "remark": row["remark"]}


def _plot_payload(row: Any) -> dict[str, Any]:
    return {"id": f"P{row['plot_id']:03d}", "farmId": f"F{row['farm_id']:03d}", "plotCode": row["plot_code"], "plotName": row["plot_name"], "areaMu": float(row["area_mu"]) if row["area_mu"] is not None else None, "location": row["location"], "irrigationMethod": row["irrigation_method"], "farmerUserId": f"U{row['farmer_user_id']:03d}" if row["farmer_user_id"] else None, "status": row["plot_status"]}


@router.get("/admin/farms")
def list_farm_archives(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    require_system_admin(user)
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT * FROM farm ORDER BY farm_id")).mappings().all()
    return [_farm_payload(row) for row in rows]


@router.post("/admin/farms", status_code=status.HTTP_201_CREATED)
def create_farm_archive(request: FarmArchiveRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user)
    admin_id = parse_resource_id(request.adminUserId, "U") if request.adminUserId else None
    with engine.begin() as connection:
        result = connection.execute(text("INSERT INTO farm(admin_user_id,farm_name,province,city,address,area_mu,farm_status,remark) VALUES(:admin,:name,:province,:city,:address,:area,:status,:remark)"), {"admin": admin_id, "name": request.farmName.strip(), "province": request.province, "city": request.city, "address": request.address, "area": request.areaMu, "status": request.status, "remark": request.remark})
        row = connection.execute(text("SELECT * FROM farm WHERE farm_id=:id"), {"id": result.lastrowid}).mappings().one()
        write_audit_log(connection, user=user, action_type="CREATE", resource_type="FARM", resource_id=f"F{result.lastrowid:03d}", description="新增橙园档案", after_data=_farm_payload(row))
    return _farm_payload(row)


@router.put("/admin/farms/{farm_id}")
def update_farm_archive(farm_id: str, request: FarmArchiveRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user); numeric_id = parse_resource_id(farm_id, "F")
    admin_id = parse_resource_id(request.adminUserId, "U") if request.adminUserId else None
    with engine.begin() as connection:
        before = connection.execute(text("SELECT * FROM farm WHERE farm_id=:id FOR UPDATE"), {"id": numeric_id}).mappings().first()
        if before is None: raise HTTPException(status_code=404, detail="FARM_NOT_FOUND")
        connection.execute(text("UPDATE farm SET admin_user_id=:admin,farm_name=:name,province=:province,city=:city,address=:address,area_mu=:area,farm_status=:status,remark=:remark WHERE farm_id=:id"), {"admin": admin_id, "name": request.farmName.strip(), "province": request.province, "city": request.city, "address": request.address, "area": request.areaMu, "status": request.status, "remark": request.remark, "id": numeric_id})
        row = connection.execute(text("SELECT * FROM farm WHERE farm_id=:id"), {"id": numeric_id}).mappings().one()
        write_audit_log(connection, user=user, action_type="UPDATE", resource_type="FARM", resource_id=f"F{numeric_id:03d}", description="修改橙园档案", before_data=_farm_payload(before), after_data=_farm_payload(row))
    return _farm_payload(row)


@router.get("/admin/plots")
def list_plot_archives(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    require_system_admin(user)
    with engine.connect() as connection: rows = connection.execute(text("SELECT * FROM plot ORDER BY plot_id")).mappings().all()
    return [_plot_payload(row) for row in rows]


@router.post("/admin/plots", status_code=status.HTTP_201_CREATED)
def create_plot_archive(request: PlotArchiveRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user); farm_id = parse_resource_id(request.farmId, "F"); farmer_id = parse_resource_id(request.farmerUserId, "U") if request.farmerUserId else None
    try:
        with engine.begin() as connection:
            result = connection.execute(text("INSERT INTO plot(farmer_user_id,farm_id,plot_code,plot_name,location,crop_name,area_mu,irrigation_method,plot_status) VALUES(:farmer,:farm,:code,:name,:location,'脐橙',:area,:method,:status)"), {"farmer": farmer_id, "farm": farm_id, "code": request.plotCode.strip(), "name": request.plotName.strip(), "location": request.location, "area": request.areaMu, "method": request.irrigationMethod, "status": request.status})
            row = connection.execute(text("SELECT * FROM plot WHERE plot_id=:id"), {"id": result.lastrowid}).mappings().one()
            write_audit_log(connection, user=user, action_type="CREATE", resource_type="PLOT", resource_id=f"P{result.lastrowid:03d}", description="新增地块档案", after_data=_plot_payload(row))
    except IntegrityError as error: raise HTTPException(status_code=409, detail="PLOT_CODE_OR_NAME_ALREADY_EXISTS") from error
    return _plot_payload(row)


@router.put("/admin/plots/{plot_id}")
def update_plot_archive(plot_id: str, request: PlotArchiveRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user); numeric_id = parse_resource_id(plot_id, "P"); farm_id = parse_resource_id(request.farmId, "F"); farmer_id = parse_resource_id(request.farmerUserId, "U") if request.farmerUserId else None
    try:
        with engine.begin() as connection:
            before = connection.execute(text("SELECT * FROM plot WHERE plot_id=:id FOR UPDATE"), {"id": numeric_id}).mappings().first()
            if before is None: raise HTTPException(status_code=404, detail="PLOT_NOT_FOUND")
            connection.execute(text("UPDATE plot SET farmer_user_id=:farmer,farm_id=:farm,plot_code=:code,plot_name=:name,location=:location,area_mu=:area,irrigation_method=:method,plot_status=:status WHERE plot_id=:id"), {"farmer": farmer_id, "farm": farm_id, "code": request.plotCode.strip(), "name": request.plotName.strip(), "location": request.location, "area": request.areaMu, "method": request.irrigationMethod, "status": request.status, "id": numeric_id})
            row = connection.execute(text("SELECT * FROM plot WHERE plot_id=:id"), {"id": numeric_id}).mappings().one()
            write_audit_log(connection, user=user, action_type="UPDATE", resource_type="PLOT", resource_id=f"P{numeric_id:03d}", description="修改地块档案", before_data=_plot_payload(before), after_data=_plot_payload(row))
    except IntegrityError as error: raise HTTPException(status_code=409, detail="PLOT_CODE_OR_NAME_ALREADY_EXISTS") from error
    return _plot_payload(row)


@router.get("/farms/{farm_id}/management-stats")
def farm_management_stats(farm_id: str, user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    numeric_id = parse_resource_id(farm_id, "F"); allowed = accessible_farm_ids(user)
    if allowed is not None and numeric_id not in allowed: raise HTTPException(status_code=403, detail="FORBIDDEN")
    with engine.connect() as connection:
        rows = connection.execute(text("""
          SELECT p.plot_id,p.plot_name,p.farmer_user_id,u.real_name,p.crop_name,
            p.planting_date,p.stage_override_code,t.template_content,
            (SELECT plot_moisture FROM plot_report pr WHERE pr.plot_id=p.plot_id ORDER BY report_datetime DESC LIMIT 1) moisture,
            (SELECT COUNT(*) FROM alert a WHERE a.plot_id=p.plot_id AND a.alert_status='active') active_alerts,
            (SELECT ROUND(100*SUM(task_status='COMPLETED')/NULLIF(COUNT(*),0),1) FROM farm_task ft WHERE ft.plot_id=p.plot_id AND ft.task_status<>'SUPERSEDED') completion_rate,
            (SELECT requested_at FROM irrigation_record ir WHERE ir.plot_id=p.plot_id AND ir.status='success' ORDER BY requested_at DESC LIMIT 1) last_irrigation
          FROM plot p LEFT JOIN users u ON u.user_id=p.farmer_user_id
          LEFT JOIN cultivation_template t ON t.template_id=p.template_id
          WHERE p.farm_id=:farm_id ORDER BY p.plot_id
        """), {"farm_id": numeric_id}).mappings().all()
    result = []
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    for row in rows:
        stage = None
        if row["template_content"] and row["planting_date"]:
            content = json.loads(row["template_content"]) if isinstance(row["template_content"], str) else row["template_content"]
            stage = resolve_stage(content, today=today, planting_date=row["planting_date"], override_code=row["stage_override_code"])
        result.append({"plotId": f"P{row['plot_id']:03d}", "plotName": row["plot_name"], "farmerName": row["real_name"], "variety": row["crop_name"], "currentStage": stage, "soilMoisture": float(row["moisture"]) if row["moisture"] is not None else None, "pendingAlerts": int(row["active_alerts"]), "taskCompletionRate": float(row["completion_rate"] or 0), "lastIrrigationAt": utc_isoformat(row["last_irrigation"])})
    return result


@router.get("/admin/audit-logs")
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, alias="pageSize", ge=1, le=200),
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    require_system_admin(user)
    with engine.connect() as connection:
        total = int(connection.execute(text("SELECT COUNT(*) FROM audit_log")).scalar_one())
        rows = connection.execute(text("SELECT l.*,u.real_name,u.username FROM audit_log l LEFT JOIN users u ON u.user_id=l.user_id ORDER BY l.created_at DESC,l.log_id DESC LIMIT :limit OFFSET :offset"), {"limit": page_size, "offset": (page-1)*page_size}).mappings().all()
    items = [{"id": f"LOG{r['log_id']:03d}", "user": r["real_name"] or r["username"], "role": r["role_code"], "action": r["action_type"], "resourceType": r["resource_type"], "resourceId": r["resource_id"], "description": r["description"], "beforeData": r["before_data"], "afterData": r["after_data"], "ip": r["ip_address"], "createdAt": utc_isoformat(r["created_at"])} for r in rows]
    return {"items": items, "total": total, "page": page, "pageSize": page_size}
