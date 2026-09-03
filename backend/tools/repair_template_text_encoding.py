"""Repair reversibly mojibaked UTF-8 template and generated-task text.

This is intentionally narrow: a value changes only when its Latin-1 byte
sequence decodes as UTF-8 and the result contains CJK characters.
"""

from __future__ import annotations

import unicodedata
from typing import Any

from sqlalchemy import text

from backend.app.db import engine


TEXT_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("crop_template", "template_id", "template_name"),
    ("crop_template", "template_id", "crop_name"),
    ("crop_template", "template_id", "province"),
    ("crop_template", "template_id", "city"),
    ("crop_template_version", "template_version_id", "change_note"),
    ("growth_stage_template", "stage_template_id", "stage_name"),
    ("growth_stage_template", "stage_template_id", "management_focus"),
    ("management_task_template", "task_template_id", "title"),
    ("management_task_template", "task_template_id", "note"),
    ("management_task", "task_id", "title"),
    ("management_task", "task_id", "note"),
)


def restored_text(value: str | None) -> str | None:
    if not value or not any(0x80 <= ord(char) <= 0xFF for char in value):
        return None
    try:
        repaired = value.encode("latin1").decode("utf-8")
    except UnicodeError:
        return None
    if repaired == value or not any("CJK" in unicodedata.name(char, "") for char in repaired):
        return None
    return repaired


def repair_template_text_encoding(connection: Any) -> int:
    repaired_count = 0
    for table, identifier, column in TEXT_COLUMNS:
        rows = connection.execute(text(f"SELECT {identifier}, {column} FROM {table} WHERE {column} IS NOT NULL FOR UPDATE")).mappings().all()
        for row in rows:
            repaired = restored_text(row[column])
            if repaired is None:
                continue
            connection.execute(text(f"UPDATE {table} SET {column}=:value WHERE {identifier}=:id"), {"value": repaired, "id": row[identifier]})
            repaired_count += 1
    return repaired_count


if __name__ == "__main__":
    with engine.begin() as connection:
        print(f"Repaired {repair_template_text_encoding(connection)} text values.")
