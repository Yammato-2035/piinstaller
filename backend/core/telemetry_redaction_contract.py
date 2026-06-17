"""
Public-safe telemetry redaction contract for rescue stick offline queue.

No server ingest, no commercial cloud logic.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

REDACTION_CONTRACT_VERSION = 1

_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d?\d)){3}|"
    r"(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4})\b"
)
_MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_HOST_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9-]{0,62}\.[a-zA-Z]{2,}\b")
_SERIAL_RE = re.compile(r"\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{10,32}\b")
_TOKEN_RE = re.compile(r"\b(?:sk|pk|api|bearer)[-_]?[a-zA-Z0-9]{12,}\b", re.I)
_USER_PATH_RE = re.compile(r"/(?:home|media|run/user)/[^/\s]+")
_BLOCKED_KEYS = frozenset(
    {
        "password",
        "passwd",
        "token",
        "api_key",
        "secret",
        "authorization",
        "private_key",
        "psk",
        "wifi_psk",
    }
)


def _hash_redact(value: str, *, prefix: str = "sha256") -> str:
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def redact_string(value: str) -> str:
    s = value
    s = _EMAIL_RE.sub("[REDACTED:email]", s)
    s = _IP_RE.sub("[REDACTED:ip]", s)
    s = _MAC_RE.sub("[REDACTED:mac]", s)
    s = _HOST_RE.sub("[REDACTED:hostname]", s)
    s = _USER_PATH_RE.sub("/[REDACTED:userpath]", s)
    if _SERIAL_RE.search(s):
        s = _SERIAL_RE.sub("[REDACTED:serial]", s)
    s = _TOKEN_RE.sub("[REDACTED:token]", s)
    return s


def redact_telemetry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Deep-redact telemetry/evidence dict for stick-local storage."""

    def walk(obj: Any, key: str = "") -> Any:
        lk = (key or "").lower()
        if lk in _BLOCKED_KEYS or any(x in lk for x in ("password", "token", "secret", "api_key")):
            return "[REDACTED:blocked_key]"
        if isinstance(obj, dict):
            return {str(k): walk(v, str(k)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(item) for item in obj]
        if isinstance(obj, str):
            return redact_string(obj)
        return obj

    redacted = walk(payload)
    if isinstance(redacted, dict):
        redacted.setdefault("redaction", {})
        if isinstance(redacted["redaction"], dict):
            redacted["redaction"].update(
                {
                    "contract_version": REDACTION_CONTRACT_VERSION,
                    "app_db_contains_raw_ip": False,
                    "network_upload_attempted": False,
                }
            )
        redacted["redacted"] = True
    return redacted if isinstance(redacted, dict) else {"payload": redacted, "redacted": True}


def redact_preview(payload: dict[str, Any]) -> dict[str, Any]:
    """Return redacted payload plus field-level diff hints for operators."""
    redacted = redact_telemetry_payload(payload)
    return {
        "contract_version": REDACTION_CONTRACT_VERSION,
        "redacted": redacted,
        "blocked_keys_removed": sorted(
            k for k in payload if str(k).lower() in _BLOCKED_KEYS
        ),
    }
