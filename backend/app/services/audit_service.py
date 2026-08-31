from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


def write_audit_log(
    connection: Any,
    *,
    user: dict[str, Any],
    action_type: str,
    resource_type: str,
    resource_id: str,
    description: str,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    """Write an audit record using the caller's transaction."""
    connection.execute(
        text(
            """
            INSERT INTO audit_log (
              user_id, role_code, action_type, resource_type, resource_id,
              description, before_data, after_data, ip_address, created_at
            ) VALUES (
              :user_id, :role_code, :action_type, :resource_type, :resource_id,
              :description, :before_data, :after_data, :ip_address, UTC_TIMESTAMP(6)
            )
            """
        ),
        {
            "user_id": user["user_id"],
            "role_code": user.get("role"),
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "description": description,
            "before_data": json.dumps(before_data, ensure_ascii=False, default=str) if before_data is not None else None,
            "after_data": json.dumps(after_data, ensure_ascii=False, default=str) if after_data is not None else None,
            "ip_address": ip_address,
        },
    )
