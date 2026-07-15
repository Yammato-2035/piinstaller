"""Failed stubs for rescue API discovery endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_valid_api_json_body(raw: str) -> bool:
    text = (raw or "").strip()
    if not text.startswith("{"):
        return False
    try:
        import json

        data = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict)


def build_rescue_health_degraded(*, rescue_version: str = "", boot_session_id: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "degraded",
        "rescue_version": rescue_version,
        "boot_session_id": boot_session_id,
        "checked_at": _utc_now(),
    }


def build_disk_inventory_failed_stub(*, rescue_version: str = "", boot_session_id: str = "") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "failed",
        "error_code": "api_endpoint_failed",
        "rescue_version": rescue_version,
        "boot_session_id": boot_session_id,
        "checked_at": _utc_now(),
        "devices": [],
    }


def build_storage_discovery_failed_stub(
    *,
    message_redacted: str = "",
    http_status: int = 500,
    rescue_version: str = "",
    boot_session_id: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "failed",
        "error_code": "api_endpoint_failed",
        "http_status": http_status,
        "message_redacted": message_redacted,
        "rescue_version": rescue_version,
        "boot_session_id": boot_session_id,
        "checked_at": _utc_now(),
        "classified": [],
    }
