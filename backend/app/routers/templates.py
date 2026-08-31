from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from ..access import parse_resource_id, require_system_admin
from ..auth import current_user
from ..db import engine, utc_isoformat
from ..services.audit_service import write_audit_log
from ..services.stage_service import validate_template_content


router = APIRouter(prefix="/api/cultivation-templates", tags=["cultivation-templates"])


class TemplateRequest(BaseModel):
    templateCode: str = Field(min_length=1, max_length=50)
    templateName: str = Field(min_length=1, max_length=100)
    varietyName: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)
    version: int = Field(ge=1)
    templateContent: dict[str, Any]
    templateStatus: str = "ACTIVE"


def _payload(row: Any) -> dict[str, Any]:
    content = row["template_content"]
    if isinstance(content, str):
        content = json.loads(content)
    return {
        "templateId": f"T{row['template_id']:03d}",
        "templateCode": row["template_code"],
        "templateName": row["template_name"],
        "varietyName": row["variety_name"],
        "region": row["region"],
        "version": row["version"],
        "templateContent": content,
        "templateStatus": row["template_status"],
        "createdBy": f"U{row['created_by']:03d}" if row["created_by"] is not None else None,
        "createdAt": utc_isoformat(row["created_at"]),
        "updatedAt": utc_isoformat(row["updated_at"]),
    }


def _validate_request(request: TemplateRequest) -> dict[str, Any]:
    if request.templateStatus not in {"ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=400, detail="INVALID_TEMPLATE_STATUS")
    try:
        return validate_template_content(request.templateContent)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("")
def list_templates(_user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT * FROM cultivation_template ORDER BY template_code, version DESC")
        ).mappings().all()
    return [_payload(row) for row in rows]


@router.get("/{template_id}")
def get_template(template_id: str, _user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    numeric_id = parse_resource_id(template_id, "T")
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT * FROM cultivation_template WHERE template_id=:template_id"),
            {"template_id": numeric_id},
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
    return _payload(row)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_template(request: TemplateRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user)
    content = _validate_request(request)
    try:
        with engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    INSERT INTO cultivation_template (
                      template_code, template_name, variety_name, region, version,
                      template_content, template_status, created_by
                    ) VALUES (
                      :code, :name, :variety, :region, :version,
                      :content, :status, :created_by
                    )
                    """
                ),
                {
                    "code": request.templateCode.strip(),
                    "name": request.templateName.strip(),
                    "variety": request.varietyName.strip(),
                    "region": request.region.strip(),
                    "version": request.version,
                    "content": json.dumps(content, ensure_ascii=False),
                    "status": request.templateStatus,
                    "created_by": user["user_id"],
                },
            )
            template_id = result.lastrowid
            write_audit_log(
                connection,
                user=user,
                action_type="CREATE",
                resource_type="CULTIVATION_TEMPLATE",
                resource_id=f"T{template_id:03d}",
                description="新增脐橙管理模板",
                after_data=request.model_dump(),
            )
            row = connection.execute(
                text("SELECT * FROM cultivation_template WHERE template_id=:template_id"),
                {"template_id": template_id},
            ).mappings().one()
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="TEMPLATE_VERSION_ALREADY_EXISTS") from error
    return _payload(row)


@router.put("/{template_id}")
def update_template(
    template_id: str,
    request: TemplateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    require_system_admin(user)
    numeric_id = parse_resource_id(template_id, "T")
    content = _validate_request(request)
    try:
        with engine.begin() as connection:
            existing = connection.execute(
                text("SELECT * FROM cultivation_template WHERE template_id=:template_id FOR UPDATE"),
                {"template_id": numeric_id},
            ).mappings().first()
            if existing is None:
                raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
            connection.execute(
                text(
                    """
                    UPDATE cultivation_template
                    SET template_code=:code, template_name=:name, variety_name=:variety,
                        region=:region, version=:version, template_content=:content,
                        template_status=:status
                    WHERE template_id=:template_id
                    """
                ),
                {
                    "code": request.templateCode.strip(),
                    "name": request.templateName.strip(),
                    "variety": request.varietyName.strip(),
                    "region": request.region.strip(),
                    "version": request.version,
                    "content": json.dumps(content, ensure_ascii=False),
                    "status": request.templateStatus,
                    "template_id": numeric_id,
                },
            )
            write_audit_log(
                connection,
                user=user,
                action_type="UPDATE",
                resource_type="CULTIVATION_TEMPLATE",
                resource_id=f"T{numeric_id:03d}",
                description="修改脐橙管理模板",
                before_data=_payload(existing),
                after_data=request.model_dump(),
            )
            row = connection.execute(
                text("SELECT * FROM cultivation_template WHERE template_id=:template_id"),
                {"template_id": numeric_id},
            ).mappings().one()
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="TEMPLATE_VERSION_ALREADY_EXISTS") from error
    return _payload(row)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> Response:
    require_system_admin(user)
    numeric_id = parse_resource_id(template_id, "T")
    with engine.begin() as connection:
        existing = connection.execute(
            text("SELECT * FROM cultivation_template WHERE template_id=:template_id FOR UPDATE"),
            {"template_id": numeric_id},
        ).mappings().first()
        if existing is None:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        used = connection.execute(
            text(
                "SELECT EXISTS(SELECT 1 FROM plot WHERE template_id=:template_id) "
                "OR EXISTS(SELECT 1 FROM farm_task WHERE template_id=:template_id)"
            ),
            {"template_id": numeric_id},
        ).scalar()
        if used:
            raise HTTPException(status_code=409, detail="TEMPLATE_IN_USE")
        write_audit_log(
            connection,
            user=user,
            action_type="DELETE",
            resource_type="CULTIVATION_TEMPLATE",
            resource_id=f"T{numeric_id:03d}",
            description="删除未使用的脐橙管理模板",
            before_data=_payload(existing),
        )
        connection.execute(
            text("DELETE FROM cultivation_template WHERE template_id=:template_id"),
            {"template_id": numeric_id},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
