"""Real verify for physical E2E backup archives."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from modules.backup_verify import verify_basic, verify_deep


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_physical_e2e_verify(
    *,
    backup_archive: Path,
    expected_file_count: int | None = None,
    expected_total_bytes: int | None = None,
    runner: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    started = _utc_now()
    if not backup_archive.is_file():
        return {
            "success": False,
            "started_at": started,
            "completed_at": _utc_now(),
            "passed": False,
            "code": "archive_missing",
            "real_operation": True,
        }

    basic_ok, basic_key, basic_detail = verify_basic(backup_archive, runner=runner)
    if not basic_ok:
        return {
            "success": False,
            "started_at": started,
            "completed_at": _utc_now(),
            "passed": False,
            "code": basic_key,
            "detail": basic_detail,
            "real_operation": True,
        }

    deep_ok, deep_key, deep_details = verify_deep(
        backup_archive,
        verify_checksums=True,
        strict_archive_manifest=False,
        runner=runner,
    )
    completed = _utc_now()
    errors = deep_details.get("errors") or []
    passed = deep_ok and not errors

    result: dict[str, Any] = {
        "success": passed,
        "started_at": started,
        "completed_at": completed,
        "passed": passed,
        "code": deep_key if passed else "verify_failed",
        "errors": errors,
        "details": deep_details,
        "real_operation": True,
    }
    if expected_file_count is not None:
        result["expected_file_count"] = expected_file_count
    if expected_total_bytes is not None:
        result["expected_total_bytes"] = expected_total_bytes
    return result
