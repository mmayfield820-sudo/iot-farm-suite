"""Conservative repair helpers for legacy UTF-8 mojibake."""

from __future__ import annotations

import unicodedata


_WINDOWS_1252_TO_BYTE: dict[int, int] = {}
for _byte_value in range(0x80, 0xA0):
    try:
        _decoded_character = bytes([_byte_value]).decode("cp1252")
    except UnicodeDecodeError:
        continue
    _WINDOWS_1252_TO_BYTE[ord(_decoded_character)] = _byte_value


def _legacy_client_bytes(value: str) -> bytes:
    # MySQL's historical latin1 behaves like Windows-1252 for defined C1
    # bytes, while some clients preserve undefined bytes as control codepoints.
    normalized = value.translate(_WINDOWS_1252_TO_BYTE)
    return normalized.encode("latin1")


def restored_text(value: str | None) -> str | None:
    """Return repaired CJK text only when the conversion is reversible.

    Some early demo rows were inserted through a ``latin1`` client connection.
    Depending on the client, bytes in the 0x80-0x9f range were decoded as
    either ISO-8859-1 controls or Windows-1252 punctuation. Do not guess when
    the value cannot be round-tripped.
    """
    if not value or not any(0x80 <= ord(char) <= 0xFF for char in value):
        return None
    for encoder in (lambda text: text.encode("latin1"), _legacy_client_bytes):
        try:
            repaired = encoder(value).decode("utf-8")
        except UnicodeError:
            continue
        if repaired != value and any("CJK" in unicodedata.name(char, "") for char in repaired):
            return repaired
    return None


def display_text(value: str | None) -> str | None:
    """Return safely repaired legacy text, otherwise the original value."""
    return restored_text(value) or value
