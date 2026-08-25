from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID

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


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    plotId: str | None = None


def business_id(prefix: str, value: int) -> str:
    return f"{prefix}{value:03d}"


def iso(value: datetime | None) -> str | None:
    return utc_isoformat(value)


def value_of(row: Any, key: str) -> Any:
    return row._mapping[key] if hasattr(row, "_mapping") else row[key]


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
                text("SELECT farm_id FROM farm WHERE admin_user_id = :user_id"),
                {"user_id": user["user_id"]},
            ).fetchall()
        else:
            rows = connection.execute(
                text("SELECT DISTINCT farm_id FROM plot WHERE farmer_user_id = :user_id"),
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
    if user["role"] == "farm_admin" and plot["admin_user_id"] == user["user_id"]:
        return dict(plot)
    if user["role"] == "farmer" and plot["farmer_user_id"] == user["user_id"]:
        return dict(plot)
    raise HTTPException(status_code=403, detail="FORBIDDEN")


def ensure_plot_manage_access(plot_id: int, user: dict[str, Any]) -> dict[str, Any]:
    plot = plot_scope(plot_id, user)
    if user["role"] == "farmer":
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return plot


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
    if user["role"] == "farm_admin" and device["admin_user_id"] == user["user_id"]:
        return dict(device)
    if user["role"] == "farmer" and device["farmer_user_id"] == user["user_id"]:
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
    return {
        "token": create_access_token(user),
        "user": {
            "id": business_id("U", user["user_id"]),
            "username": user["username"],
            "role": user["role"],
        },
    }


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
            plot_filter += " AND farmer_user_id = :user_id"
            params["user_id"] = user["user_id"]

        plots = connection.execute(
            text(
                f"""
                SELECT plot_id, farm_id, plot_name
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
        clauses.append("(f.admin_user_id = :user_id OR d.plot_id IS NULL)")
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append("p.farmer_user_id = :user_id")
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
    if user["role"] == "farm_admin" and device["admin_user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    if user["role"] == "farmer" and device["farmer_user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
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
        clauses.append("f.admin_user_id = :user_id")
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append("p.farmer_user_id = :user_id")
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
        clauses.append("f.admin_user_id = :user_id")
        params["user_id"] = user["user_id"]
    elif user["role"] == "farmer":
        clauses.append("p.farmer_user_id = :user_id")
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
    ensure_plot_manage_access(numeric_plot_id, user)
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
    if request.plotId is not None:
        plot_scope(parse_resource_id(request.plotId, "P"), user)
    service_url = os.getenv("AI_SERVICE_URL", "").rstrip("/")
    if not service_url:
        raise HTTPException(status_code=503, detail="AI_SERVICE_UNAVAILABLE")
    payload = json.dumps(
        {
            "sessionId": session_id,
            "message": request.message,
            "plotId": request.plotId,
            "userId": business_id("U", user["user_id"]),
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
