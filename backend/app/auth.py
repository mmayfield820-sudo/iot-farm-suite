from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from .db import engine


_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret or secret == "change-me-in-local-env":
        raise RuntimeError("JWT_SECRET must be configured in .env")
    return secret


def _expiry_minutes() -> int:
    return int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def _role_codes_for(connection: Any, user_id: int) -> list[str]:
    rows = connection.execute(
        text(
            """
            SELECT r.role_code
            FROM user_role_rel AS ur
            JOIN roles AS r ON r.role_id = ur.role_id
            WHERE ur.user_id = :user_id
              AND ur.status = 'active'
            ORDER BY FIELD(r.role_code, 'system_admin', 'farm_admin', 'farmer')
            """
        ),
        {"user_id": user_id},
    ).scalars().all()
    return list(rows)


def _role_for(connection: Any, user_id: int) -> str:
    roles = _role_codes_for(connection, user_id)
    if roles:
        return roles[0]
    # Backward-compatible fallback before migration 006 has been applied.
    if connection.execute(
        text("SELECT 1 FROM farm WHERE admin_user_id = :user_id LIMIT 1"),
        {"user_id": user_id},
    ).scalar():
        return "farm_admin"
    return "farmer"


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        user = connection.execute(
            text(
                """
                SELECT user_id, username, password_hash, activation_status
                FROM users
                WHERE username = :username AND user_status = 'active'
                """
            ),
            {"username": username},
        ).mappings().first()

        if user is None or not verify_password(password, user["password_hash"]):
            return None

        # A pre-created employee account may already have a temporary password,
        # but it must not be usable until the employee finishes activation.
        if user["activation_status"] != "ACTIVATED":
            raise HTTPException(status_code=403, detail="ACCOUNT_NOT_ACTIVATED")

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": _role_for(connection, user["user_id"]),
            "roles": _role_codes_for(connection, user["user_id"]),
        }


def create_access_token(user: dict[str, Any]) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user["user_id"]),
        "iat": now,
        "exp": now + timedelta(minutes=_expiry_minutes()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_ALGORITHM)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")

    try:
        payload = jwt.decode(credentials.credentials, _jwt_secret(), algorithms=[_ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")

    with engine.connect() as connection:
        user = connection.execute(
            text(
                """
                SELECT user_id, username
                FROM users
                WHERE user_id = :user_id
                  AND user_status = 'active'
                  AND activation_status = 'ACTIVATED'
                """
            ),
            {"user_id": user_id},
        ).mappings().first()

        if user is None:
            raise HTTPException(status_code=401, detail="UNAUTHORIZED")

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": _role_for(connection, user["user_id"]),
            "roles": _role_codes_for(connection, user["user_id"]),
        }
