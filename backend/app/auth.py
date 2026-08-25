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


def _role_for(connection: Any, user_id: int) -> str:
    is_system_admin = connection.execute(
        text(
            """
            SELECT 1
            FROM user_role_rel AS ur
            JOIN roles AS r ON r.role_id = ur.role_id
            WHERE ur.user_id = :user_id
              AND ur.status = 'active'
              AND r.role_code = 'system_admin'
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).scalar()
    if is_system_admin:
        return "system_admin"

    is_farm_admin = connection.execute(
        text("SELECT 1 FROM farm WHERE admin_user_id = :user_id LIMIT 1"),
        {"user_id": user_id},
    ).scalar()
    if is_farm_admin:
        return "farm_admin"

    return "farmer"


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with engine.connect() as connection:
        user = connection.execute(
            text(
                """
                SELECT user_id, username, password_hash
                FROM users
                WHERE username = :username AND user_status = 'active'
                """
            ),
            {"username": username},
        ).mappings().first()

        if user is None or not verify_password(password, user["password_hash"]):
            return None

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": _role_for(connection, user["user_id"]),
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
                WHERE user_id = :user_id AND user_status = 'active'
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
        }
