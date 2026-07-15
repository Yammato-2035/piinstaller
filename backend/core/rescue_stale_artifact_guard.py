"""Stale artifact guards for MSI evidence collectors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_artifact_metadata(
    *,
    rescue_version: str = "",
    boot_session_id: str = "",
    source_run_id: str = "",
    generated_by: str = "",
    error_reason: str = "",
) -> dict[str, Any]:
    return {
        "rescue_version": rescue_version,
        "collector_version": rescue_version,
        "boot_session_id": boot_session_id,
        "collected_at": _utc_now(),
        "source_run_id": source_run_id,
        "stale": False,
        "generated_by": generated_by,
        "error_reason": error_reason or None,
    }


def build_failed_stub(
    *,
    error_code: str,
    errors: list[str],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = dict(metadata or {})
    return {
        "schema_version": 1,
        "status": "failed",
        "error_code": error_code,
        "errors": errors,
        "checked_at": _utc_now(),
        "secrets_exposed": False,
        "current_result_valid": False,
        **meta,
    }
