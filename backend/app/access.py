from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import text

from .db import engine, parse_id


def parse_resource_id(value: str, prefix: str) -> int:
    try:
        return parse_id(value, prefix)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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


def require_plot_access(plot_id: int, user: dict[str, Any]) -> dict[str, Any]:
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
    if user["role"] == "farm_admin" and plot["farm_id"] in (accessible_farm_ids(user) or set()):
        return dict(plot)
    if user["role"] == "farmer":
        with engine.connect() as connection:
            scoped = connection.execute(
                text("SELECT 1 FROM farmer_plot_scope WHERE user_id=:user_id AND plot_id=:plot_id"),
                {"user_id": user["user_id"], "plot_id": plot_id},
            ).scalar()
        if plot["farmer_user_id"] == user["user_id"] or scoped:
            return dict(plot)
    raise HTTPException(status_code=403, detail="FORBIDDEN")


def require_system_admin(user: dict[str, Any]) -> None:
    if user["role"] != "system_admin":
        raise HTTPException(status_code=403, detail="FORBIDDEN")
