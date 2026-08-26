from __future__ import annotations

import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .auth import authenticate, create_access_token, current_user
from .db import check_database, engine, parse_id, utc_isoformat, utc_naive
from .mqtt import MqttService


mqtt_service = MqttService()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    mqtt_service.start()
    try:
        yield
    finally:
        mqtt_service.stop()

app = FastAPI(
    title="Smart Farm API",
    version="0.1.0",
    description="Smart agriculture backend service",
    lifespan=lifespan,
)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistrationRequest(BaseModel):
    username: str = Field(min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=72)
    real_name: str = Field(min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role_codes: list[str] = Field(min_length=1)
    farm_ids: list[str] = Field(default_factory=list)
    plot_ids: list[str] = Field(default_factory=list)


class UserSaveRequest(BaseModel):
    username: str = Field(min_length=4, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    name: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    active: bool = True
    role_codes: list[str] = Field(min_length=1)
    farm_ids: list[str] = Field(default_factory=list)
    plot_ids: list[str] = Field(default_factory=list)


class UserActiveRequest(BaseModel):
    active: bool


class RejectRegistrationRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=255)


class CommandCreateRequest(BaseModel):
    action: str
    activationType: str = "manual"


class DeviceCreateRequest(BaseModel):
    deviceNo: str = Field(min_length=1, max_length=100)
    deviceUuid: str
    type: str
    plotId: str | None = None


class DeviceBindRequest(BaseModel):
    plotId: str


class AlertRuleRequest(BaseModel):
    plotId: str
    soilMoistureThreshold: float = Field(ge=0, le=100)
    irrigationLength: int = Field(default=0, ge=0)
    irrigationInterval: int = Field(default=0, ge=0)


class IrrigationSettingsRequest(BaseModel):
    soilMoistureThreshold: float = Field(ge=0, le=100)
    irrigationDuration: int = Field(ge=0, le=1440)
    irrigationInterval: int = Field(ge=0, le=10080)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    plotId: str | None = None


def business_id(prefix: str, value: int) -> str:
    return f"{prefix}{value:03d}"


def iso(value: datetime | None) -> str | None:
    return utc_isoformat(value)


def value_of(row: Any, key: str) -> Any:
    return row._mapping[key] if hasattr(row, "_mapping") else row[key]


ROLE_CODES = {"farmer", "farm_admin", "system_admin"}
FRONTEND_ROLE_CODES = {
    "farmer": "farmer",
    "farm_admin": "farmAdmin",
    "system_admin": "systemAdmin",
}


def canonical_role_codes(role_codes: list[str]) -> list[str]:
    aliases = {"farmAdmin": "farm_admin", "systemAdmin": "system_admin"}
    normalized = list(dict.fromkeys(aliases.get(role, role) for role in role_codes))
    if not normalized or any(role not in ROLE_CODES for role in normalized):
        raise HTTPException(status_code=400, detail="INVALID_ROLE_CODES")
    return normalized


def resource_ids(values: list[str], prefix: str) -> list[int]:
    return list(dict.fromkeys(parse_resource_id(value, prefix) for value in values))


def json_values(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return [str(item) for item in value] if isinstance(value, list) else []


def password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def ensure_system_admin(user: dict[str, Any]) -> None:
    if user["role"] != "system_admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")


def device_payload(row: Any) -> dict[str, Any]:
    return {
        "id": business_id("D", value_of(row, "device_id")),
        "deviceNo": value_of(row, "device_code"),
        "deviceUuid": value_of(row, "device_uuid"),
        "type": value_of(row, "device_type"),
        "plotId": (
            business_id("P", value_of(row, "plot_id"))
            if value_of(row, "plot_id") is not None
            else None
        ),
        "status": value_of(row, "status"),
        "lastSeenAt": iso(value_of(row, "last_heartbeat")),
    }


def accessible_farm_ids(user: dict[str, Any]) -> set[int] | None:
    if user["role"] == "system_admin":
        return None

    with engine.connect() as connection:
        if user["role"] == "farm_admin":
            rows = connection.execute(
                text(
                    "SELECT farm_id FROM farm WHERE admin_user_id = :user_id "
                    "UNION SELECT farm_id FROM farm_admin_scope WHERE user_id = :user_id"
                ),
                {"user_id": user["user_id"]},
            ).fetchall()
        else:
            rows = connection.execute(
                text(
                    "SELECT DISTINCT farm_id FROM plot WHERE farmer_user_id = :user_id "
                    "UNION SELECT DISTINCT p.farm_id FROM farmer_plot_scope AS s "
                    "JOIN plot AS p ON p.plot_id = s.plot_id WHERE s.user_id = :user_id"
                ),
                {"user_id": user["user_id"]},
            ).fetchall()
    return {row.farm_id for row in rows}


def ensure_farm_access(user: dict[str, Any], farm_id: int) -> None:
    allowed_farms = accessible_farm_ids(user)
    if allowed_farms is not None and farm_id not in allowed_farms:
        raise HTTPException(status_code=403, detail="FORBIDDEN")


def parse_resource_id(value: str, prefix: str) -> int:
    try:
        return parse_id(value, prefix)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def normalized_uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError) as error:
        raise HTTPException(status_code=400, detail="deviceUuid must be a valid UUID") from error


def plot_scope(plot_id: int, user: dict[str, Any]) -> dict[str, Any]:
    with engine.connect() as connection:
        plot = connection.execute(
            text(
                """
                SELECT p.plot_id, p.farm_id, p.farmer_user_id, f.admin_user_id
                FROM plot AS p
                JOIN farm AS f ON f.farm_id = p.farm_id
                WHERE p.plot_id = :plot_id
                """
            ),
            {"plot_id": plot_id},
        ).mappings().first()
    if plot is None:
        raise HTTPException(status_code=404, detail="PLOT_NOT_FOUND")
    if user["role"] == "system_admin":
        return dict(plot)
    if user["role"] == "farm_admin" and plot["farm_id"] in accessible_farm_ids(user):
        return dict(plot)
    if user["role"] == "farmer":
        with engine.connect() as connection:
            allowed = connection.execute(
                text(
                    "SELECT 1 FROM farmer_plot_scope "
                    "WHERE user_id = :user_id AND plot_id = :plot_id"
                ),
                {"user_id": user["user_id"], "plot_id": plot_id},
            ).scalar()
        if plot["farmer_user_id"] == user["user_id"] or allowed:
            return dict(plot)
    raise HTTPException(status_code=403, detail="FORBIDDEN")


def ensure_plot_manage_access(plot_id: int, user: dict[str, Any]) -> dict[str, Any]:
    plot = plot_scope(plot_id, user)
    if user["role"] == "farmer":
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return plot


def assistant_plot_context(plot_id: int) -> dict[str, Any]:
    """Build the least-privilege plot snapshot that may leave the business API."""
    with engine.connect() as connection:
        plot = connection.execute(
            text(
                """
                SELECT p.plot_name, p.crop_name, p.location,
                       t.soil_moisture_threshold
                FROM plot AS p
                LEFT JOIN threshold_config AS t ON t.plot_id = p.plot_id
                WHERE p.plot_id = :plot_id
                """
            ),
            {"plot_id": plot_id},
        ).mappings().one()
        report = connection.execute(
            text(
                """
                SELECT plot_moisture, temperature, report_datetime
                FROM plot_report
                WHERE plot_id = :plot_id
                ORDER BY report_datetime DESC
                LIMIT 1
                """
            ),
            {"plot_id": plot_id},
        ).mappings().first()
        irrigation_device = connection.execute(
            text(
                """
                SELECT status FROM device
                WHERE plot_id = :plot_id AND device_type = 'irrigation'
                LIMIT 1
                """
            ),
            {"plot_id": plot_id},
        ).mappings().first()
        last_command = connection.execute(
            text(
                """
                SELECT action_type, status
                FROM irrigation_record
                WHERE plot_id = :plot_id
                ORDER BY requested_at DESC, record_id DESC
                LIMIT 1
                """
            ),
            {"plot_id": plot_id},
        ).mappings().first()

    context: dict[str, Any] = {
        "plotName": plot["plot_name"],
        "cropName": plot["crop_name"],
        "location": plot["location"],
        "soilMoistureThreshold": (
            float(plot["soil_moisture_threshold"])
            if plot["soil_moisture_threshold"] is not None
            else None
        ),
        "irrigationDeviceOnline": (
            irrigation_device["status"] == "online"
            if irrigation_device is not None
            else False
        ),
    }
    if report is not None:
        context.update(
            {
                "soilMoisture": float(report["plot_moisture"]),
                "temperature": float(report["temperature"]),
                "dataUpdatedAt": iso(report["report_datetime"]),
            }
        )
    if last_command is not None and last_command["status"] == "success":
        context["irrigationState"] = last_command["action_type"]
    return context


def device_scope(device_id: int, user: dict[str, Any], *, allow_unbound_admin: bool = False) -> dict[str, Any]:
    with engine.connect() as connection:
        device = connection.execute(
            text(
                """
                SELECT d.device_id, d.device_code, d.device_uuid, d.device_type,
                       d.plot_id, d.status, d.last_heartbeat,
                       p.farmer_user_id, f.admin_user_id
                FROM device AS d
                LEFT JOIN plot AS p ON p.plot_id = d.plot_id
                LEFT JOIN farm AS f ON f.farm_id = p.farm_id
                WHERE d.device_id = :device_id
                """
            ),
            {"device_id": device_id},
        ).mappings().first()
    if device is None:
        raise HTTPException(status_code=404, detail="DEVICE_NOT_FOUND")
    if user["role"] == "system_admin":
        return dict(device)
    if device["plot_id"] is None:
        if allow_unbound_admin and user["role"] == "farm_admin":
            return dict(device)
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    if user["role"] == "farm_admin" and device["plot_id"] is not None:
        with engine.connect() as connection:
            allowed = connection.execute(
                text(
                    "SELECT 1 FROM farm_admin_scope AS s "
                    "JOIN plot AS p ON p.farm_id = s.farm_id "
                    "WHERE s.user_id = :user_id AND p.plot_id = :plot_id"
                ),
                {"user_id": user["user_id"], "plot_id": device["plot_id"]},
            ).scalar()
        if device["admin_user_id"] == user["user_id"] or allowed:
            return dict(device)
    if user["role"] == "farmer" and device["plot_id"] is not None:
        with engine.connect() as connection:
            allowed = connection.execute(
                text(
                    "SELECT 1 FROM farmer_plot_scope "
                    "WHERE user_id = :user_id AND plot_id = :plot_id"
                ),
                {"user_id": user["user_id"], "plot_id": device["plot_id"]},
            ).scalar()
        if device["farmer_user_id"] == user["user_id"] or allowed:
            return dict(device)
    raise HTTPException(status_code=403, detail="FORBIDDEN")


def ensure_device_manage_access(device_id: int, user: dict[str, Any], *, allow_unbound_admin: bool = False) -> dict[str, Any]:
    device = device_scope(device_id, user, allow_unbound_admin=allow_unbound_admin)
    if user["role"] == "farmer":
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return device


def command_payload(row: Any) -> dict[str, Any]:
    return {
        "commandId": value_of(row, "command_id"),
        "deviceId": business_id("D", value_of(row, "device_id")),
        "deviceUuid": value_of(row, "device_uuid"),
        "action": f"irrigation_{value_of(row, 'action_type')}",
        "activationType": value_of(row, "activation_type"),
        "status": value_of(row, "status"),
        "requestedAt": iso(value_of(row, "requested_at")),
        "executedAt": iso(value_of(row, "executed_at")),
    }


def alert_payload(row: Any) -> dict[str, Any]:
    return {
        "id": business_id("A", value_of(row, "alert_id")),
        "plotId": business_id("P", value_of(row, "plot_id")),
        "deviceId": (
            business_id("D", value_of(row, "device_id"))
            if value_of(row, "device_id") is not None
            else None
        ),
        "type": value_of(row, "alert_type"),
        "description": value_of(row, "alert_description"),
        "value": float(value_of(row, "alert_value")) if value_of(row, "alert_value") is not None else None,
        "threshold": float(value_of(row, "alert_threshold")) if value_of(row, "alert_threshold") is not None else None,
        "status": value_of(row, "alert_status"),
        "triggeredAt": iso(value_of(row, "alert_datetime")),
        "handledAt": iso(value_of(row, "handled_at")),
    }


def alert_rule_payload(row: Any) -> dict[str, Any]:
    return {
        "id": business_id("R", value_of(row, "config_id")),
        "plotId": business_id("P", value_of(row, "plot_id")),
        "soilMoistureThreshold": float(value_of(row, "soil_moisture_threshold")),
        "irrigationLength": value_of(row, "irrigation_length"),
        "irrigationInterval": value_of(row, "irrigation_interval"),
        "updatedAt": iso(value_of(row, "updated_at")),
    }


def irrigation_record_payload(row: Any) -> dict[str, Any]:
    return {
        "recordId": business_id("IR", value_of(row, "record_id")),
        "commandId": value_of(row, "command_id"),
        "plotId": business_id("P", value_of(row, "plot_id")),
        "deviceId": business_id("D", value_of(row, "device_id")),
        "action": f"irrigation_{value_of(row, 'action_type')}",
        "activationType": value_of(row, "activation_type"),
        "status": value_of(row, "status"),
        "requestedAt": iso(value_of(row, "requested_at")),
        "executedAt": iso(value_of(row, "executed_at")),
    }


def user_payload(connection: Any, user_id: int) -> dict[str, Any]:
    user = connection.execute(
        text(
            """
            SELECT user_id, username, real_name, email, phone, user_status
            FROM users WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().one()
    roles = connection.execute(
        text(
            """
            SELECT r.role_code FROM user_role_rel AS ur
            JOIN roles AS r ON r.role_id = ur.role_id
            WHERE ur.user_id = :user_id AND ur.status = 'active'
            ORDER BY FIELD(r.role_code, 'system_admin', 'farm_admin', 'farmer')
            """
        ),
        {"user_id": user_id},
    ).scalars().all()
    farm_ids = connection.execute(
        text(
            """
            SELECT farm_id FROM farm WHERE admin_user_id = :user_id
            UNION SELECT farm_id FROM farm_admin_scope WHERE user_id = :user_id
            ORDER BY 1
            """
        ),
        {"user_id": user_id},
    ).scalars().all()
    plot_ids = connection.execute(
        text(
            """
            SELECT plot_id FROM plot WHERE farmer_user_id = :user_id
            UNION SELECT plot_id FROM farmer_plot_scope WHERE user_id = :user_id
            ORDER BY 1
            """
        ),
        {"user_id": user_id},
    ).scalars().all()
    return {
        "id": business_id("U", user["user_id"]),
        "username": user["username"],
        "name": user["real_name"] or user["username"],
        "displayName": user["real_name"] or user["username"],
        "email": user["email"],
        "phone": user["phone"],
        "active": user["user_status"] == "active",
        "roles": [FRONTEND_ROLE_CODES[role] for role in roles],
        "roleCodes": roles,
        "farmIds": [business_id("F", value) for value in farm_ids],
        "plotIds": [business_id("P", value) for value in plot_ids],
    }


def registration_payload(row: Any) -> dict[str, Any]:
    roles = json_values(value_of(row, "role_codes"))
    return {
        "id": business_id("REG", value_of(row, "application_id")),
        "applicationId": business_id("REG", value_of(row, "application_id")),
        "username": value_of(row, "username"),
        "realName": value_of(row, "real_name"),
        "email": value_of(row, "email"),
        "phone": value_of(row, "phone"),
        "roles": [FRONTEND_ROLE_CODES[role] for role in roles],
        "roleCodes": roles,
        "farmIds": [business_id("F", int(value)) for value in json_values(value_of(row, "farm_ids"))],
        "plotIds": [business_id("P", int(value)) for value in json_values(value_of(row, "plot_ids"))],
        "status": value_of(row, "application_status"),
        "createdAt": iso(value_of(row, "created_at")),
        "reviewedAt": iso(value_of(row, "reviewed_at")),
        "rejectReason": value_of(row, "reject_reason"),
    }


def replace_user_assignments(
    connection: Any,
    user_id: int,
    role_codes: list[str],
    farm_ids: list[int],
    plot_ids: list[int],
) -> None:
    connection.execute(text("DELETE FROM user_role_rel WHERE user_id = :user_id"), {"user_id": user_id})
    connection.execute(text("DELETE FROM farm_admin_scope WHERE user_id = :user_id"), {"user_id": user_id})
    connection.execute(text("DELETE FROM farmer_plot_scope WHERE user_id = :user_id"), {"user_id": user_id})
    connection.execute(
        text(
            """
            INSERT INTO user_role_rel (user_id, role_id, status)
            SELECT :user_id, role_id, 'active' FROM roles
            WHERE role_code IN :role_codes
            """
        ).bindparams(bindparam("role_codes", expanding=True)),
        {"user_id": user_id, "role_codes": role_codes},
    )
    if "farm_admin" in role_codes and farm_ids:
        connection.execute(
            text("INSERT INTO farm_admin_scope (user_id, farm_id) VALUES (:user_id, :farm_id)"),
            [{"user_id": user_id, "farm_id": farm_id} for farm_id in farm_ids],
        )
    if "farmer" in role_codes and plot_ids:
        connection.execute(
            text("INSERT INTO farmer_plot_scope (user_id, plot_id) VALUES (:user_id, :plot_id)"),
            [{"user_id": user_id, "plot_id": plot_id} for plot_id in plot_ids],
        )


def ensure_existing_resources(connection: Any, farm_ids: list[int], plot_ids: list[int]) -> None:
    if farm_ids:
        count = connection.execute(
            text("SELECT COUNT(*) FROM farm WHERE farm_id IN :farm_ids").bindparams(
                bindparam("farm_ids", expanding=True)
            ),
            {"farm_ids": farm_ids},
        ).scalar_one()
        if count != len(farm_ids):
            raise HTTPException(status_code=404, detail="FARM_NOT_FOUND")
    if plot_ids:
        count = connection.execute(
            text("SELECT COUNT(*) FROM plot WHERE plot_id IN :plot_ids").bindparams(
                bindparam("plot_ids", expanding=True)
            ),
            {"plot_ids": plot_ids},
        ).scalar_one()
        if count != len(plot_ids):
            raise HTTPException(status_code=404, detail="PLOT_NOT_FOUND")


@app.get("/health")
def health() -> dict[str, str]:
    try:
        check_database()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok", "database": "ok"}


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict[str, Any]:
    user = authenticate(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")
    with engine.connect() as connection:
        profile = user_payload(connection, user["user_id"])
    return {
        "token": create_access_token(user),
        "user": {**profile, "role": user["role"]},
    }


@app.get("/api/registration-resources")
def registration_resources() -> dict[str, list[dict[str, Any]]]:
    """Public, read-only identifiers used by the registration form."""
    with engine.connect() as connection:
        farms = connection.execute(
            text("SELECT farm_id, farm_name, city, address FROM farm ORDER BY farm_id")
        ).mappings().all()
        plots = connection.execute(
            text(
                """
                SELECT plot_id, farm_id, plot_name, crop_name, description
                FROM plot ORDER BY plot_id
                """
            )
        ).mappings().all()
    return {
        "farms": [
            {
                "id": business_id("F", row["farm_id"]),
                "name": row["farm_name"],
                "city": row["city"],
                "address": row["address"],
                "active": True,
            }
            for row in farms
        ],
        "plots": [
            {
                "id": business_id("P", row["plot_id"]),
                "plotNo": business_id("P", row["plot_id"]),
                "farmId": business_id("F", row["farm_id"]),
                "name": row["plot_name"],
                "crop": row["crop_name"],
                "note": row["description"],
            }
            for row in plots
        ],
    }


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(request: RegistrationRequest) -> dict[str, Any]:
    role_codes = canonical_role_codes(request.role_codes)
    if "system_admin" in role_codes:
        raise HTTPException(status_code=400, detail="SYSTEM_ADMIN_REGISTRATION_NOT_ALLOWED")
    farm_ids = resource_ids(request.farm_ids, "F")
    plot_ids = resource_ids(request.plot_ids, "P")
    if "farm_admin" in role_codes and not farm_ids:
        raise HTTPException(status_code=400, detail="FARM_SCOPE_REQUIRED")
    if "farmer" in role_codes and not plot_ids:
        raise HTTPException(status_code=400, detail="PLOT_SCOPE_REQUIRED")
    with engine.begin() as connection:
        ensure_existing_resources(connection, farm_ids, plot_ids)
        if connection.execute(
            text("SELECT 1 FROM users WHERE username = :username"),
            {"username": request.username},
        ).scalar():
            raise HTTPException(status_code=409, detail="USERNAME_ALREADY_EXISTS")
        if connection.execute(
            text("SELECT 1 FROM registration_application WHERE username = :username"),
            {"username": request.username},
        ).scalar():
            raise HTTPException(status_code=409, detail="REGISTRATION_ALREADY_EXISTS")
        try:
            result = connection.execute(
                text(
                    """
                    INSERT INTO registration_application (
                        username, password_hash, real_name, email, phone,
                        role_codes, farm_ids, plot_ids
                    ) VALUES (
                        :username, :password_hash, :real_name, :email, :phone,
                        :role_codes, :farm_ids, :plot_ids
                    )
                    """
                ),
                {
                    "username": request.username,
                    "password_hash": password_hash(request.password),
                    "real_name": request.real_name.strip(),
                    "email": request.email or None,
                    "phone": request.phone or None,
                    "role_codes": json.dumps(role_codes),
                    "farm_ids": json.dumps(farm_ids),
                    "plot_ids": json.dumps(plot_ids),
                },
            )
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="REGISTRATION_ALREADY_EXISTS") from error
        row = connection.execute(
            text("SELECT * FROM registration_application WHERE application_id = :application_id"),
            {"application_id": result.lastrowid},
        ).mappings().one()
    return registration_payload(row)


@app.get("/api/registration-applications")
def list_registration_applications(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    ensure_system_admin(user)
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT * FROM registration_application ORDER BY created_at DESC, application_id DESC")
        ).mappings().all()
    return [registration_payload(row) for row in rows]


@app.put("/api/registration-applications/{application_id}/approve")
def approve_registration(application_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    ensure_system_admin(user)
    numeric_id = parse_resource_id(application_id, "REG")
    with engine.begin() as connection:
        application = connection.execute(
            text("SELECT * FROM registration_application WHERE application_id = :application_id FOR UPDATE"),
            {"application_id": numeric_id},
        ).mappings().first()
        if application is None:
            raise HTTPException(status_code=404, detail="REGISTRATION_NOT_FOUND")
        if application["application_status"] != "pending":
            raise HTTPException(status_code=409, detail="REGISTRATION_NOT_PENDING")
        if connection.execute(
            text("SELECT 1 FROM users WHERE username = :username"),
            {"username": application["username"]},
        ).scalar():
            raise HTTPException(status_code=409, detail="USERNAME_ALREADY_EXISTS")
        result = connection.execute(
            text(
                """
                INSERT INTO users (username, password_hash, real_name, email, phone)
                VALUES (:username, :password_hash, :real_name, :email, :phone)
                """
            ),
            dict(application),
        )
        role_codes = json_values(application["role_codes"])
        replace_user_assignments(
            connection,
            result.lastrowid,
            role_codes,
            [int(value) for value in json_values(application["farm_ids"])],
            [int(value) for value in json_values(application["plot_ids"])],
        )
        connection.execute(
            text(
                """
                UPDATE registration_application
                SET application_status = 'approved', reviewed_at = :reviewed_at,
                    reviewed_by = :reviewed_by
                WHERE application_id = :application_id
                """
            ),
            {"application_id": numeric_id, "reviewed_at": datetime.now(UTC).replace(tzinfo=None), "reviewed_by": user["user_id"]},
        )
        row = connection.execute(
            text("SELECT * FROM registration_application WHERE application_id = :application_id"),
            {"application_id": numeric_id},
        ).mappings().one()
    return registration_payload(row)


@app.put("/api/registration-applications/{application_id}/reject")
def reject_registration(
    application_id: str,
    request: RejectRegistrationRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    ensure_system_admin(user)
    numeric_id = parse_resource_id(application_id, "REG")
    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE registration_application
                SET application_status = 'rejected', reject_reason = :reason,
                    reviewed_at = :reviewed_at, reviewed_by = :reviewed_by
                WHERE application_id = :application_id AND application_status = 'pending'
                """
            ),
            {"application_id": numeric_id, "reason": request.reason.strip(), "reviewed_at": datetime.now(UTC).replace(tzinfo=None), "reviewed_by": user["user_id"]},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=409, detail="REGISTRATION_NOT_PENDING")
        row = connection.execute(
            text("SELECT * FROM registration_application WHERE application_id = :application_id"),
            {"application_id": numeric_id},
        ).mappings().one()
    return registration_payload(row)


@app.get("/api/users")
def list_users(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    ensure_system_admin(user)
    with engine.connect() as connection:
        user_ids = connection.execute(text("SELECT user_id FROM users ORDER BY user_id")).scalars().all()
        return [user_payload(connection, user_id) for user_id in user_ids]


def save_user_record(
    request: UserSaveRequest,
    user_id: int | None,
) -> tuple[dict[str, Any], str | None]:
    role_codes = canonical_role_codes(request.role_codes)
    farm_ids = resource_ids(request.farm_ids, "F")
    plot_ids = resource_ids(request.plot_ids, "P")
    if "farm_admin" in role_codes and not farm_ids:
        raise HTTPException(status_code=400, detail="FARM_SCOPE_REQUIRED")
    if "farmer" in role_codes and not plot_ids:
        raise HTTPException(status_code=400, detail="PLOT_SCOPE_REQUIRED")
    temporary_password: str | None = None
    with engine.begin() as connection:
        ensure_existing_resources(connection, farm_ids, plot_ids)
        if user_id is None:
            temporary_password = f"Tmp-{secrets.token_urlsafe(9)}"
            try:
                result = connection.execute(
                    text(
                        """
                        INSERT INTO users (username, password_hash, real_name, email, phone, user_status)
                        VALUES (:username, :password_hash, :real_name, :email, :phone, :user_status)
                        """
                    ),
                    {
                        "username": request.username,
                        "password_hash": password_hash(temporary_password),
                        "real_name": request.name or request.username,
                        "email": request.email or None,
                        "phone": request.phone or None,
                        "user_status": "active" if request.active else "disabled",
                    },
                )
            except IntegrityError as error:
                raise HTTPException(status_code=409, detail="USERNAME_OR_EMAIL_ALREADY_EXISTS") from error
            numeric_user_id = result.lastrowid
        else:
            existing = connection.execute(
                text("SELECT 1 FROM users WHERE user_id = :user_id"), {"user_id": user_id}
            ).scalar()
            if not existing:
                raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
            try:
                connection.execute(
                    text(
                        """
                        UPDATE users
                        SET real_name = :real_name, email = :email, phone = :phone,
                            user_status = :user_status
                        WHERE user_id = :user_id
                        """
                    ),
                    {
                        "user_id": user_id,
                        "real_name": request.name or request.username,
                        "email": request.email or None,
                        "phone": request.phone or None,
                        "user_status": "active" if request.active else "disabled",
                    },
                )
            except IntegrityError as error:
                raise HTTPException(status_code=409, detail="EMAIL_ALREADY_EXISTS") from error
            numeric_user_id = user_id
        replace_user_assignments(connection, numeric_user_id, role_codes, farm_ids, plot_ids)
        return user_payload(connection, numeric_user_id), temporary_password


@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserSaveRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    ensure_system_admin(user)
    saved, temporary_password = save_user_record(request, None)
    return {**saved, "temporaryPassword": temporary_password}


@app.put("/api/users/{user_id}")
def update_user(
    user_id: str,
    request: UserSaveRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    ensure_system_admin(user)
    numeric_user_id = parse_resource_id(user_id, "U")
    saved, _ = save_user_record(request, numeric_user_id)
    return saved


@app.put("/api/users/{user_id}/active")
def update_user_active(
    user_id: str,
    request: UserActiveRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    ensure_system_admin(user)
    numeric_user_id = parse_resource_id(user_id, "U")
    if numeric_user_id == user["user_id"] and not request.active:
        raise HTTPException(status_code=400, detail="CANNOT_DISABLE_CURRENT_USER")
    with engine.begin() as connection:
        result = connection.execute(
            text("UPDATE users SET user_status = :status WHERE user_id = :user_id"),
            {"user_id": numeric_user_id, "status": "active" if request.active else "disabled"},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
        return user_payload(connection, numeric_user_id)


@app.post("/api/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, str]:
    ensure_system_admin(user)
    numeric_user_id = parse_resource_id(user_id, "U")
    temporary_password = f"Tmp-{secrets.token_urlsafe(9)}"
    with engine.begin() as connection:
        result = connection.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE user_id = :user_id"),
            {"user_id": numeric_user_id, "password_hash": password_hash(temporary_password)},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    return {"temporaryPassword": temporary_password}


@app.get("/api/farms")
def list_farms(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, str]]:
    allowed_farms = accessible_farm_ids(user)
    with engine.connect() as connection:
        if allowed_farms is None:
            rows = connection.execute(
                text("SELECT farm_id, farm_name FROM farm ORDER BY farm_id")
            ).fetchall()
        elif not allowed_farms:
            rows = []
        else:
            statement = text(
                "SELECT farm_id, farm_name FROM farm "
                "WHERE farm_id IN :farm_ids ORDER BY farm_id"
            ).bindparams(bindparam("farm_ids", expanding=True))
            rows = connection.execute(
                statement, {"farm_ids": list(allowed_farms)}
            ).fetchall()

    return [
        {"id": business_id("F", row.farm_id), "name": row.farm_name}
        for row in rows
    ]


@app.get("/api/farms/{farm_id}/overview")
def farm_overview(
    farm_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    try:
        numeric_farm_id = parse_id(farm_id, "F")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    ensure_farm_access(user, numeric_farm_id)

    with engine.connect() as connection:
        plot_filter = "farm_id = :farm_id"
        params: dict[str, Any] = {"farm_id": numeric_farm_id}
        if user["role"] == "farmer":
            plot_filter += (
                " AND (farmer_user_id = :user_id OR EXISTS ("
                "SELECT 1 FROM farmer_plot_scope AS s "
                "WHERE s.user_id = :user_id AND s.plot_id = plot.plot_id))"
            )
            params["user_id"] = user["user_id"]

        plots = connection.execute(
            text(
                f"""
                SELECT plot_id, farm_id, plot_name, location, crop_name, description
                FROM plot
                WHERE {plot_filter}
                ORDER BY plot_id
                """
            ),
            params,
        ).fetchall()

        result = []
        for plot in plots:
            devices = connection.execute(
                text(
                    """
                           SELECT device_id, device_code, device_uuid, device_type,
                           plot_id, status, last_heartbeat
                    FROM device
                    WHERE plot_id = :plot_id
                    ORDER BY device_id
                    """
                ),
                {"plot_id": plot.plot_id},
            ).fetchall()
            report = connection.execute(
                text(
                    """
                    SELECT plot_moisture, temperature, report_datetime
                    FROM plot_report
                    WHERE plot_id = :plot_id
                    ORDER BY report_datetime DESC
                    LIMIT 1
                    """
                ),
                {"plot_id": plot.plot_id},
            ).first()

            metrics = []
            if report:
                metrics = [
                    {
                        "type": "humidity",
                        "value": float(report.plot_moisture),
                        "unit": "%",
                        "ts": iso(report.report_datetime),
                    },
                    {
                        "type": "temperature",
                        "value": float(report.temperature),
                        "unit": "C",
                        "ts": iso(report.report_datetime),
                    },
                ]

            result.append(
                {
                    "plot": {
                        "id": business_id("P", plot.plot_id),
                        "farmId": business_id("F", plot.farm_id),
                        "name": plot.plot_name,
                        "location": plot.location,
                        "crop": plot.crop_name,
                        "description": plot.description,
                    },
                    "latestMetrics": metrics,
                    "devices": [device_payload(device) for device in devices],
                }
            )
    return result


@app.get("/api/devices")
def list_devices(
    plot_id: str | None = Query(default=None, alias="plotId"),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    clauses = []

    if plot_id is not None:
        try:
            params["plot_id"] = parse_id(plot_id, "P")
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))
        clauses.append("d.plot_id = :plot_id")

    if user["role"] == "farm_admin":
        clauses.append(
            "(f.admin_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farm_admin_scope AS s "
            "WHERE s.user_id = :user_id AND s.farm_id = f.farm_id) OR d.plot_id IS NULL)"
        )
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append(
            "(p.farmer_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farmer_plot_scope AS s "
            "WHERE s.user_id = :user_id AND s.plot_id = p.plot_id))"
        )
        params["user_id"] = user["user_id"]

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT d.device_id, d.device_code, d.device_uuid, d.device_type,
                       d.plot_id, d.status, d.last_heartbeat
                FROM device AS d
                LEFT JOIN plot AS p ON p.plot_id = d.plot_id
                LEFT JOIN farm AS f ON f.farm_id = p.farm_id
                {where}
                ORDER BY d.device_id
                """
            ),
            params,
        ).fetchall()
    return [device_payload(row) for row in rows]


@app.post("/api/devices", status_code=status.HTTP_201_CREATED)
def create_device(
    request: DeviceCreateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    device_no = request.deviceNo.strip()
    if not device_no:
        raise HTTPException(status_code=400, detail="deviceNo must not be blank")
    if request.type not in {"temperature", "humidity", "irrigation"}:
        raise HTTPException(status_code=400, detail="unsupported device type")
    plot_id = parse_resource_id(request.plotId, "P") if request.plotId else None
    if plot_id is None and user["role"] != "system_admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    if plot_id is not None:
        ensure_plot_manage_access(plot_id, user)

    with engine.begin() as connection:
        try:
            result = connection.execute(
                text(
                    """
                    INSERT INTO device (device_code, device_uuid, device_type, plot_id)
                    VALUES (:device_code, :device_uuid, :device_type, :plot_id)
                    """
                ),
                {
                    "device_code": device_no,
                    "device_uuid": normalized_uuid(request.deviceUuid),
                    "device_type": request.type,
                    "plot_id": plot_id,
                },
            )
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="DEVICE_ALREADY_EXISTS") from error
        device_id = result.lastrowid
        row = connection.execute(
            text(
                """
                SELECT device_id, device_code, device_uuid, device_type,
                       plot_id, status, last_heartbeat
                FROM device WHERE device_id = :device_id
                """
            ),
            {"device_id": device_id},
        ).mappings().one()
    return device_payload(row)


@app.post("/api/devices/{device_id}/bind")
def bind_device(
    device_id: str,
    request: DeviceBindRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_device_id = parse_resource_id(device_id, "D")
    target_plot_id = parse_resource_id(request.plotId, "P")
    ensure_device_manage_access(numeric_device_id, user, allow_unbound_admin=True)
    ensure_plot_manage_access(target_plot_id, user)
    with engine.begin() as connection:
        try:
            connection.execute(
                text("UPDATE device SET plot_id = :plot_id WHERE device_id = :device_id"),
                {"plot_id": target_plot_id, "device_id": numeric_device_id},
            )
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="PLOT_DEVICE_TYPE_EXISTS") from error
        row = connection.execute(
            text(
                """
                SELECT device_id, device_code, device_uuid, device_type,
                       plot_id, status, last_heartbeat
                FROM device WHERE device_id = :device_id
                """
            ),
            {"device_id": numeric_device_id},
        ).mappings().one()
    return device_payload(row)


@app.delete("/api/devices/{device_id}/bind", status_code=status.HTTP_204_NO_CONTENT)
def unbind_device(
    device_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> None:
    numeric_device_id = parse_resource_id(device_id, "D")
    ensure_device_manage_access(numeric_device_id, user)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE device SET plot_id = NULL, status = 'offline' WHERE device_id = :device_id"),
            {"device_id": numeric_device_id},
        )


@app.get("/api/devices/{device_id}/status")
def get_device_status(
    device_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    device = device_scope(parse_resource_id(device_id, "D"), user)
    return {
        "deviceId": business_id("D", device["device_id"]),
        "status": device["status"],
        "lastSeenAt": iso(device["last_heartbeat"]),
    }


@app.post("/api/devices/{device_id}/commands", status_code=202)
def create_device_command(
    device_id: str,
    request: CommandCreateRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    try:
        numeric_device_id = parse_id(device_id, "D")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    with engine.connect() as connection:
        device = connection.execute(
            text(
                """
                SELECT d.device_id, d.device_uuid, d.device_type,
                       p.plot_id, p.farmer_user_id, f.farm_id, f.admin_user_id
                FROM device AS d
                JOIN plot AS p ON p.plot_id = d.plot_id
                JOIN farm AS f ON f.farm_id = p.farm_id
                WHERE d.device_id = :device_id
                """
            ),
            {"device_id": numeric_device_id},
        ).mappings().first()
    if device is None:
        raise HTTPException(status_code=404, detail="DEVICE_NOT_FOUND")
    plot_scope(device["plot_id"], user)
    if device["device_type"] != "irrigation":
        raise HTTPException(status_code=409, detail="DEVICE_NOT_IRRIGATION")

    action = request.action
    action = {"irrigation_on": "on", "irrigation_off": "off"}.get(action, action)
    if action not in {"on", "off"}:
        raise HTTPException(status_code=400, detail="action must be irrigation_on, irrigation_off, on, or off")
    try:
        command = mqtt_service.publish_control_command(
            device_uuid=device["device_uuid"],
            switch=action,
            operator_id=user["user_id"],
            activation_type=request.activationType,
        )
        return {
            "commandId": command["commandId"],
            "deviceId": business_id("D", numeric_device_id),
            "deviceUuid": device["device_uuid"],
            "action": f"irrigation_{action}",
            "activationType": request.activationType,
            "status": command["status"],
            "requestedAt": command["requestedAt"],
            "executedAt": None,
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


@app.get("/api/commands/{command_id}")
def get_command(
    command_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    with engine.connect() as connection:
        command = connection.execute(
            text(
                """
                SELECT r.command_id, r.device_id, d.device_uuid, r.plot_id,
                       r.action_type, r.activation_type, r.status,
                       r.requested_at, r.executed_at
                FROM irrigation_record AS r
                JOIN device AS d ON d.device_id = r.device_id
                WHERE r.command_id = :command_id
                """
            ),
            {"command_id": command_id},
        ).mappings().first()
    if command is None:
        raise HTTPException(status_code=404, detail="COMMAND_NOT_FOUND")
    plot_scope(command["plot_id"], user)
    return command_payload(command)


@app.get("/api/plots/{plot_id}/metrics")
def list_plot_metrics(
    plot_id: str,
    metric_type: str = Query(alias="type"),
    from_value: datetime = Query(alias="from"),
    to_value: datetime = Query(alias="to"),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    numeric_plot_id = parse_resource_id(plot_id, "P")
    plot_scope(numeric_plot_id, user)
    if metric_type not in {"temperature", "humidity"}:
        raise HTTPException(status_code=400, detail="type must be temperature or humidity")
    try:
        from_utc = utc_naive(from_value)
        to_utc = utc_naive(to_value)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if from_utc >= to_utc:
        raise HTTPException(status_code=400, detail="from must be before to")

    value_column = "temperature" if metric_type == "temperature" else "plot_moisture"
    unit = "C" if metric_type == "temperature" else "%"
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT {value_column} AS metric_value, report_datetime
                FROM plot_report
                WHERE plot_id = :plot_id
                  AND report_datetime >= :from_utc
                  AND report_datetime < :to_utc
                ORDER BY report_datetime
                """
            ),
            {"plot_id": numeric_plot_id, "from_utc": from_utc, "to_utc": to_utc},
        ).mappings().all()
    return [
        {
            "type": metric_type,
            "value": float(row["metric_value"]),
            "unit": unit,
            "ts": iso(row["report_datetime"]),
        }
        for row in rows
    ]


@app.get("/api/irrigation/records")
def list_irrigation_records(
    plot_id: str = Query(alias="plotId"),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    numeric_plot_id = parse_resource_id(plot_id, "P")
    plot_scope(numeric_plot_id, user)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT record_id, command_id, plot_id, device_id, action_type,
                       activation_type, status, requested_at, executed_at
                FROM irrigation_record
                WHERE plot_id = :plot_id
                ORDER BY requested_at DESC, record_id DESC
                """
            ),
            {"plot_id": numeric_plot_id},
        ).mappings().all()
    return [irrigation_record_payload(row) for row in rows]


@app.get("/api/plots/{plot_id}/irrigation-settings")
def get_irrigation_settings(
    plot_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_plot_id = parse_resource_id(plot_id, "P")
    plot_scope(numeric_plot_id, user)
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT soil_moisture_threshold, irrigation_length,
                       irrigation_interval, updated_at
                FROM threshold_config
                WHERE plot_id = :plot_id
                """
            ),
            {"plot_id": numeric_plot_id},
        ).mappings().first()
    if row is None:
        return {
            "plotId": business_id("P", numeric_plot_id),
            "soilMoistureThreshold": 35,
            "irrigationDuration": 30,
            "irrigationInterval": 60,
            "updatedAt": None,
        }
    return {
        "plotId": business_id("P", numeric_plot_id),
        "soilMoistureThreshold": float(value_of(row, "soil_moisture_threshold")),
        "irrigationDuration": value_of(row, "irrigation_length"),
        "irrigationInterval": value_of(row, "irrigation_interval"),
        "updatedAt": iso(value_of(row, "updated_at")),
    }


@app.put("/api/plots/{plot_id}/irrigation-settings")
def update_irrigation_settings(
    plot_id: str,
    request: IrrigationSettingsRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_plot_id = parse_resource_id(plot_id, "P")
    plot_scope(numeric_plot_id, user)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO threshold_config (
                    plot_id, soil_moisture_threshold, irrigation_length,
                    irrigation_interval, updated_by
                ) VALUES (
                    :plot_id, :soil_moisture_threshold, :irrigation_length,
                    :irrigation_interval, :updated_by
                )
                ON DUPLICATE KEY UPDATE
                    soil_moisture_threshold = VALUES(soil_moisture_threshold),
                    irrigation_length = VALUES(irrigation_length),
                    irrigation_interval = VALUES(irrigation_interval),
                    updated_by = VALUES(updated_by)
                """
            ),
            {
                "plot_id": numeric_plot_id,
                "soil_moisture_threshold": request.soilMoistureThreshold,
                "irrigation_length": request.irrigationDuration,
                "irrigation_interval": request.irrigationInterval,
                "updated_by": user["user_id"],
            },
        )
        row = connection.execute(
            text(
                """
                SELECT soil_moisture_threshold, irrigation_length, irrigation_interval, updated_at
                FROM threshold_config
                WHERE plot_id = :plot_id
                """
            ),
            {"plot_id": numeric_plot_id},
        ).mappings().one()
    return {
        "plotId": business_id("P", numeric_plot_id),
        "soilMoistureThreshold": float(value_of(row, "soil_moisture_threshold")),
        "irrigationDuration": value_of(row, "irrigation_length"),
        "irrigationInterval": value_of(row, "irrigation_interval"),
        "updatedAt": iso(value_of(row, "updated_at")),
    }


@app.get("/api/weather/forecast")
def weather_forecast(
    plot_id: str = Query(alias="plotId"),
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    """Proxy weather data for an authorized plot without exposing provider credentials."""
    numeric_plot_id = parse_resource_id(plot_id, "P")
    plot_scope(numeric_plot_id, user)
    service_url = os.getenv("WEATHER_SERVICE_URL", "").rstrip("/")
    if not service_url:
        raise HTTPException(status_code=503, detail="WEATHER_SERVICE_UNAVAILABLE")

    separator = "&" if "?" in service_url else "?"
    target = f"{service_url}{separator}{urlencode({'plotId': business_id('P', numeric_plot_id)})}"
    try:
        with urlopen(target, timeout=float(os.getenv("WEATHER_SERVICE_TIMEOUT_SECONDS", "10"))) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        raise HTTPException(status_code=503, detail="WEATHER_SERVICE_UNAVAILABLE") from error
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="WEATHER_SERVICE_INVALID_RESPONSE")
    current = result.get("current", result)
    if not isinstance(current, dict):
        raise HTTPException(status_code=502, detail="WEATHER_SERVICE_INVALID_RESPONSE")
    return {
        "current": current,
        "hourly": result.get("hourly", []),
        "daily": result.get("daily", []),
    }


@app.get("/api/alerts")
def list_alerts(
    plot_id: str | None = Query(default=None, alias="plotId"),
    alert_status: str | None = Query(default=None, alias="status"),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if plot_id is not None:
        numeric_plot_id = parse_resource_id(plot_id, "P")
        plot_scope(numeric_plot_id, user)
        clauses.append("a.plot_id = :plot_id")
        params["plot_id"] = numeric_plot_id
    elif user["role"] == "farm_admin":
        clauses.append(
            "(f.admin_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farm_admin_scope AS s "
            "WHERE s.user_id = :user_id AND s.farm_id = f.farm_id))"
        )
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append(
            "(p.farmer_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farmer_plot_scope AS s "
            "WHERE s.user_id = :user_id AND s.plot_id = p.plot_id))"
        )
        params["user_id"] = user["user_id"]
    if alert_status is not None:
        if alert_status not in {"active", "acknowledged", "recovered"}:
            raise HTTPException(status_code=400, detail="invalid alert status")
        clauses.append("a.alert_status = :alert_status")
        params["alert_status"] = alert_status
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT a.alert_id, a.plot_id, a.device_id, a.alert_type,
                       a.alert_description, a.alert_value, a.alert_threshold,
                       a.alert_status, a.alert_datetime, a.handled_at
                FROM alert AS a
                JOIN plot AS p ON p.plot_id = a.plot_id
                JOIN farm AS f ON f.farm_id = p.farm_id
                {where}
                ORDER BY a.alert_datetime DESC, a.alert_id DESC
                """
            ),
            params,
        ).mappings().all()
    return [alert_payload(row) for row in rows]


@app.post("/api/alerts/{alert_id}/ack")
def acknowledge_alert(
    alert_id: str,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_alert_id = parse_resource_id(alert_id, "A")
    with engine.begin() as connection:
        alert = connection.execute(
            text("SELECT plot_id FROM alert WHERE alert_id = :alert_id"),
            {"alert_id": numeric_alert_id},
        ).mappings().first()
        if alert is None:
            raise HTTPException(status_code=404, detail="ALERT_NOT_FOUND")
        plot_scope(alert["plot_id"], user)
        connection.execute(
            text(
                """
                UPDATE alert
                SET alert_status = 'acknowledged', handled_by = :user_id,
                    handled_at = :handled_at
                WHERE alert_id = :alert_id AND alert_status = 'active'
                """
            ),
            {
                "alert_id": numeric_alert_id,
                "user_id": user["user_id"],
                "handled_at": datetime.now(UTC).replace(tzinfo=None),
            },
        )
        row = connection.execute(
            text(
                """
                SELECT alert_id, plot_id, device_id, alert_type, alert_description,
                       alert_value, alert_threshold, alert_status, alert_datetime,
                       handled_at
                FROM alert WHERE alert_id = :alert_id
                """
            ),
            {"alert_id": numeric_alert_id},
        ).mappings().one()
    return alert_payload(row)


@app.get("/api/alert-rules")
def list_alert_rules(
    plot_id: str | None = Query(default=None, alias="plotId"),
    user: dict[str, Any] = Depends(current_user),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if plot_id is not None:
        numeric_plot_id = parse_resource_id(plot_id, "P")
        plot_scope(numeric_plot_id, user)
        clauses.append("t.plot_id = :plot_id")
        params["plot_id"] = numeric_plot_id
    elif user["role"] == "farm_admin":
        clauses.append(
            "(f.admin_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farm_admin_scope AS s "
            "WHERE s.user_id = :user_id AND s.farm_id = f.farm_id))"
        )
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append(
            "(p.farmer_user_id = :user_id OR EXISTS ("
            "SELECT 1 FROM farmer_plot_scope AS s "
            "WHERE s.user_id = :user_id AND s.plot_id = p.plot_id))"
        )
        params["user_id"] = user["user_id"]
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT t.config_id, t.plot_id, t.soil_moisture_threshold,
                       t.irrigation_length, t.irrigation_interval, t.updated_at
                FROM threshold_config AS t
                JOIN plot AS p ON p.plot_id = t.plot_id
                JOIN farm AS f ON f.farm_id = p.farm_id
                {where}
                ORDER BY t.plot_id
                """
            ),
            params,
        ).mappings().all()
    return [alert_rule_payload(row) for row in rows]


@app.post("/api/alert-rules")
def save_alert_rule(
    request: AlertRuleRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    numeric_plot_id = parse_resource_id(request.plotId, "P")
    # Farmers may configure the threshold of their own plots. Device binding
    # remains an administrator-only operation through ensure_plot_manage_access.
    plot_scope(numeric_plot_id, user)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO threshold_config (
                    plot_id, soil_moisture_threshold, irrigation_length,
                    irrigation_interval, updated_by
                ) VALUES (
                    :plot_id, :threshold, :length, :interval, :updated_by
                )
                ON DUPLICATE KEY UPDATE
                    soil_moisture_threshold = VALUES(soil_moisture_threshold),
                    irrigation_length = VALUES(irrigation_length),
                    irrigation_interval = VALUES(irrigation_interval),
                    updated_by = VALUES(updated_by)
                """
            ),
            {
                "plot_id": numeric_plot_id,
                "threshold": request.soilMoistureThreshold,
                "length": request.irrigationLength,
                "interval": request.irrigationInterval,
                "updated_by": user["user_id"],
            },
        )
        row = connection.execute(
            text(
                """
                SELECT config_id, plot_id, soil_moisture_threshold,
                       irrigation_length, irrigation_interval, updated_at
                FROM threshold_config WHERE plot_id = :plot_id
                """
            ),
            {"plot_id": numeric_plot_id},
        ).mappings().one()
    return alert_rule_payload(row)


@app.post("/api/chat/sessions/{session_id}/messages")
def send_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    if request.plotId is not None:
        numeric_plot_id = parse_resource_id(request.plotId, "P")
        plot_scope(numeric_plot_id, user)
        context = assistant_plot_context(numeric_plot_id)
    service_url = os.getenv("AI_SERVICE_URL", "").rstrip("/")
    if not service_url:
        raise HTTPException(status_code=503, detail="AI_SERVICE_UNAVAILABLE")
    payload = json.dumps(
        {
            "sessionId": session_id,
            "message": request.message,
            "plotId": request.plotId,
            "userId": business_id("U", user["user_id"]),
            "context": context,
        }
    ).encode("utf-8")
    target = f"{service_url}/chat/sessions/{quote(session_id, safe='')}/messages"
    try:
        with urlopen(
            Request(target, data=payload, headers={"Content-Type": "application/json"}),
            timeout=float(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "10")),
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
        raise HTTPException(status_code=503, detail="AI_SERVICE_UNAVAILABLE") from error
    if not isinstance(result, dict) or not isinstance(result.get("answer"), str):
        raise HTTPException(status_code=502, detail="AI_SERVICE_INVALID_RESPONSE")
    sources = result.get("sources", [])
    if not isinstance(sources, list) or not all(isinstance(source, str) for source in sources):
        raise HTTPException(status_code=502, detail="AI_SERVICE_INVALID_RESPONSE")
    return {"sessionId": session_id, "answer": result["answer"], "sources": sources}
