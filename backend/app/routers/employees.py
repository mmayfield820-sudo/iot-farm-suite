from __future__ import annotations

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.exc import IntegrityError

from ..access import require_system_admin
from ..auth import current_user
from ..db import engine
from ..services.audit_service import write_audit_log


router = APIRouter(prefix="/api", tags=["employees"])


class EmployeeRow(BaseModel):
    employeeNo: str = Field(default="", max_length=50)
    name: str = Field(default="", max_length=50)
    phone: str = Field(default="", max_length=20)
    email: str | None = Field(default=None, max_length=100)
    role: str = Field(default="", max_length=50)
    farmCode: str | None = None
    plotCodes: list[str] = Field(default_factory=list)


class ImportRequest(BaseModel):
    rows: list[EmployeeRow] = Field(min_length=1, max_length=1000)


class ActivationVerifyRequest(BaseModel):
    identifier: str | None = Field(default=None, max_length=50)
    employeeNo: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    activationCode: str


class ActivationCompleteRequest(BaseModel):
    verificationToken: str
    username: str = Field(min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)
    phone: str = Field(min_length=6, max_length=20)
    email: str | None = Field(default=None, max_length=100)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _password_hash(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _jwt_secret() -> str:
    value = os.getenv("JWT_SECRET")
    if not value: raise RuntimeError("JWT_SECRET must be configured")
    return value


def _farm_id(connection: Any, code: str | None) -> int | None:
    if not code: return None
    normalized = code.strip().upper()
    if normalized.startswith("F") and normalized[1:].isdigit():
        value = int(normalized[1:])
        return value if connection.execute(text("SELECT 1 FROM farm WHERE farm_id=:id"), {"id": value}).scalar() else None
    return None


def _plot_ids(connection: Any, codes: list[str]) -> tuple[list[int], list[str]]:
    normalized = [code.strip() for code in codes if code.strip()]
    if not normalized: return [], []
    rows = connection.execute(text("SELECT plot_id,plot_code FROM plot WHERE plot_code IN :codes").bindparams(bindparam("codes", expanding=True)), {"codes": normalized}).mappings().all()
    found = {row["plot_code"]: int(row["plot_id"]) for row in rows}
    return [found[code] for code in normalized if code in found], [code for code in normalized if code not in found]


def _preview(connection: Any, rows: list[EmployeeRow]) -> dict[str, Any]:
    valid: list[dict[str, Any]] = []; invalid: list[dict[str, Any]] = []; seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        reasons: list[str] = []; employee_no = row.employeeNo.strip()
        if not employee_no: reasons.append("工号不能为空")
        if not row.name.strip(): reasons.append("姓名不能为空")
        if len(row.phone.strip()) < 6: reasons.append("手机号格式不正确")
        if row.role not in {"farmer", "farm_admin"}: reasons.append("角色必须是 farmer 或 farm_admin")
        if employee_no in seen: reasons.append("导入文件内工号重复")
        seen.add(employee_no)
        if connection.execute(text("SELECT 1 FROM users WHERE employee_no=:no"), {"no": employee_no}).scalar(): reasons.append("工号已存在")
        if connection.execute(text("SELECT 1 FROM users WHERE phone=:phone"), {"phone": row.phone.strip()}).scalar(): reasons.append("手机号已存在")
        farm_id = _farm_id(connection, row.farmCode)
        if row.role == "farm_admin" and farm_id is None: reasons.append("农场管理员必须填写有效农场编号，如 F001")
        plot_ids, missing = _plot_ids(connection, row.plotCodes)
        if row.role == "farmer" and not plot_ids: reasons.append("农户至少需要一个有效地块编号")
        if missing: reasons.append("地块编号不存在：" + ",".join(missing))
        if farm_id and plot_ids:
            wrong = connection.execute(text("SELECT plot_code FROM plot WHERE plot_id IN :ids AND farm_id<>:farm").bindparams(bindparam("ids", expanding=True)), {"ids": plot_ids, "farm": farm_id}).scalars().all()
            if wrong: reasons.append("地块不属于指定农场：" + ",".join(wrong))
        payload = {**row.model_dump(), "employeeNo": employee_no, "phone": row.phone.strip(), "farmId": farm_id, "plotIds": plot_ids, "rowNumber": index}
        (invalid if reasons else valid).append({**payload, "errorReasons": reasons})
    return {"validRows": valid, "invalidRows": invalid, "validCount": len(valid), "invalidCount": len(invalid)}


@router.post("/admin/users/import/preview")
def preview_import(request: ImportRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user)
    with engine.connect() as connection: return _preview(connection, request.rows)


@router.post("/admin/users/import/confirm", status_code=status.HTTP_201_CREATED)
def confirm_import(request: ImportRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user)
    try:
        with engine.begin() as connection:
            preview = _preview(connection, request.rows)
            if preview["invalidRows"]: raise HTTPException(status_code=422, detail="IMPORT_CONTAINS_INVALID_ROWS")
            created: list[dict[str, Any]] = []
            for row in preview["validRows"]:
                code = secrets.token_urlsafe(8)
                pending_username = f"pending_{row['employeeNo']}"
                result = connection.execute(text("""
              INSERT INTO users(username,real_name,password_hash,email,phone,employee_no,activation_status,activation_token_hash,user_status)
              VALUES(:username,:name,:password,:email,:phone,:employee_no,'PENDING',:token,'active')
            """), {"username": pending_username, "name": row["name"], "password": _password_hash(secrets.token_urlsafe(24)), "email": row["email"] or None, "phone": row["phone"], "employee_no": row["employeeNo"], "token": _hash(code)})
                user_id = int(result.lastrowid)
                connection.execute(text("INSERT INTO user_role_rel(user_id,role_id,status) SELECT :user_id,role_id,'active' FROM roles WHERE role_code=:role"), {"user_id": user_id, "role": row["role"]})
                if row["role"] == "farm_admin": connection.execute(text("INSERT INTO farm_admin_scope(user_id,farm_id) VALUES(:user,:farm)"), {"user": user_id, "farm": row["farmId"]})
                if row["role"] == "farmer": connection.execute(text("INSERT INTO farmer_plot_scope(user_id,plot_id) VALUES(:user,:plot)"), [{"user": user_id, "plot": plot_id} for plot_id in row["plotIds"]])
                write_audit_log(connection, user=user, action_type="IMPORT", resource_type="USER", resource_id=f"U{user_id:03d}", description="导入员工待激活账号", after_data={"employeeNo": row["employeeNo"], "role": row["role"]})
                created.append({"userId": f"U{user_id:03d}", "employeeNo": row["employeeNo"], "name": row["name"], "activationCode": code})
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="EMPLOYEE_ACCOUNT_CONFLICT") from error
    return {"createdCount": len(created), "users": created}


@router.post("/admin/users/{user_id}/reset-activation")
def reset_activation(user_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_system_admin(user)
    if not user_id.upper().startswith("U") or not user_id[1:].isdigit(): raise HTTPException(status_code=400, detail="INVALID_USER_ID")
    numeric_id = int(user_id[1:]); code = secrets.token_urlsafe(8)
    with engine.begin() as connection:
        result = connection.execute(text("UPDATE users SET activation_status='PENDING',activation_token_hash=:token,activated_at=NULL WHERE user_id=:id"), {"token": _hash(code), "id": numeric_id})
        if result.rowcount == 0: raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
        write_audit_log(connection, user=user, action_type="RESET_ACTIVATION", resource_type="USER", resource_id=f"U{numeric_id:03d}", description="重置员工激活凭证")
    return {"userId": f"U{numeric_id:03d}", "activationCode": code, "activationStatus": "PENDING"}


@router.post("/auth/activation/verify")
def verify_activation(request: ActivationVerifyRequest) -> dict[str, Any]:
    identifier = (request.identifier or request.employeeNo or request.phone or "").strip()
    if not identifier or not request.activationCode.strip():
        raise HTTPException(status_code=422, detail="ACTIVATION_FIELDS_REQUIRED")
    with engine.connect() as connection:
        employee = connection.execute(text("SELECT * FROM users WHERE (employee_no=:identifier OR phone=:identifier) AND activation_status='PENDING'"), {"identifier": identifier}).mappings().first()
        if employee is None or not secrets.compare_digest(employee["activation_token_hash"] or "", _hash(request.activationCode.strip())): raise HTTPException(status_code=401, detail="ACTIVATION_VERIFICATION_FAILED")
        roles = connection.execute(text("SELECT r.role_code FROM user_role_rel ur JOIN roles r ON r.role_id=ur.role_id WHERE ur.user_id=:id AND ur.status='active'"), {"id": employee["user_id"]}).scalars().all()
        farms = connection.execute(text("SELECT CONCAT('F',LPAD(f.farm_id,3,'0')) AS id,f.farm_name AS name FROM farm_admin_scope s JOIN farm f ON f.farm_id=s.farm_id WHERE s.user_id=:id"), {"id": employee["user_id"]}).mappings().all()
        plots = connection.execute(text("SELECT CONCAT('P',LPAD(p.plot_id,3,'0')) AS id,p.plot_name AS name FROM farmer_plot_scope s JOIN plot p ON p.plot_id=s.plot_id WHERE s.user_id=:id"), {"id": employee["user_id"]}).mappings().all()
    token = jwt.encode({"sub": str(employee["user_id"]), "purpose": "activation", "exp": datetime.now(UTC)+timedelta(minutes=15)}, _jwt_secret(), algorithm="HS256")
    return {"verificationToken": token, "employeeNo": employee["employee_no"], "name": employee["real_name"], "roles": list(roles), "farmIds": [row["id"] for row in farms], "plotIds": [row["id"] for row in plots], "farmScopes": [dict(row) for row in farms], "plotScopes": [dict(row) for row in plots], "email": employee["email"], "phone": employee["phone"]}


@router.post("/auth/activation/complete")
def complete_activation(request: ActivationCompleteRequest) -> dict[str, Any]:
    try:
        payload = jwt.decode(request.verificationToken, _jwt_secret(), algorithms=["HS256"])
        if payload.get("purpose") != "activation": raise ValueError
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError): raise HTTPException(status_code=401, detail="ACTIVATION_TOKEN_INVALID")
    try:
        with engine.begin() as connection:
            employee = connection.execute(text("SELECT * FROM users WHERE user_id=:id AND activation_status='PENDING' FOR UPDATE"), {"id": user_id}).mappings().first()
            if employee is None: raise HTTPException(status_code=409, detail="ACCOUNT_NOT_PENDING_ACTIVATION")
            phone = request.phone.strip()
            if connection.execute(text("SELECT 1 FROM users WHERE phone=:phone AND user_id<>:id"), {"phone": phone, "id": user_id}).scalar(): raise HTTPException(status_code=409, detail="PHONE_ALREADY_EXISTS")
            connection.execute(text("UPDATE users SET username=:username,password_hash=:password,phone=:phone,email=:email,activation_status='ACTIVATED',activation_token_hash=NULL,activated_at=UTC_TIMESTAMP(6) WHERE user_id=:id"), {"username": request.username, "password": _password_hash(request.password), "phone": phone, "email": request.email or employee["email"], "id": user_id})
            write_audit_log(connection, user={"user_id": user_id, "role": "employee"}, action_type="ACTIVATE", resource_type="USER", resource_id=f"U{user_id:03d}", description="员工完成账号激活")
    except IntegrityError as error: raise HTTPException(status_code=409, detail="USERNAME_OR_EMAIL_ALREADY_EXISTS") from error
    return {"userId": f"U{user_id:03d}", "username": request.username, "activationStatus": "ACTIVATED"}
