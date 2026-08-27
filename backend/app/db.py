from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL


_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


def _database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", "mysql://farm:farm@127.0.0.1:3306/farm")
    if raw_url.startswith("mysql://"):
        return "mysql+pymysql://" + raw_url[len("mysql://") :]
    return raw_url


_url = _database_url()
_engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}
if _url.startswith("mysql+pymysql://"):
    # DATETIME values are intentionally naive in MySQL, so keep every
    # connection's session clock in UTC for CURRENT_TIMESTAMP defaults.
    _engine_options["connect_args"] = {"init_command": "SET time_zone = '+00:00'"}

engine: Engine = create_engine(_url, **_engine_options)


def check_database() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def utc_isoformat(value: datetime | None) -> str | None:
    """Serialize a UTC instant with an explicit ``Z`` suffix.

    MySQL DATETIME values come back without timezone metadata; by convention
    those values are UTC. Aware values are converted rather than relabeled.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def utc_naive(value: datetime) -> datetime:
    """Convert an API datetime to the UTC-naive representation used by MySQL."""
    if value.tzinfo is None:
        raise ValueError("datetime must include a UTC offset such as Z")
    return value.astimezone(UTC).replace(tzinfo=None)


def parse_id(value: str, prefix: str) -> int:
    if value.isdigit():
        return int(value)
    if value.startswith(prefix) and value[len(prefix) :].isdigit():
        return int(value[len(prefix) :])
    raise ValueError(f"invalid {prefix} id: {value}")
