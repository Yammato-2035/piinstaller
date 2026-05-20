"""Top-level telemetry fields for backup status.json and API snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_bytes_human(num: int | float | None) -> str:
    if num is None:
        return "—"
    try:
        n = float(num)
    except (TypeError, ValueError):
        return "—"
    if n < 0:
        n = 0.0
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    u = 0
    while n >= 1024.0 and u < len(units) - 1:
        n /= 1024.0
        u += 1
    if u == 0:
        return f"{int(n)} {units[0]}"
    return f"{n:.2f} {units[u]}"


def format_rate_human(bytes_per_sec: float | None) -> str:
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "—"
    return f"{format_bytes_human(bytes_per_sec)}/s"


def sync_status_telemetry(
    status: dict[str, Any],
    *,
    phase: str | None = None,
    last_status_message: str | None = None,
    last_error_code: str | None = None,
    last_error_message: str | None = None,
    compression_detail: dict[str, Any] | None = None,
    progress_optional: dict[str, Any] | None = None,
) -> None:
    """
    Mirror progress_optional + compression_detail onto status root for dashboards.
    Mutates status in place.
    """
    po = progress_optional if progress_optional is not None else status.get("progress_optional")
    if not isinstance(po, dict):
        po = {}

    if phase is not None:
        prev = str(status.get("phase") or "")
        if phase != prev:
            status["phase_started_at"] = _now_iso()
        status["phase"] = phase
    elif po.get("phase") and not status.get("phase"):
        status["phase"] = po.get("phase")

    written = po.get("bytes_current")
    if written is not None:
        try:
            wb = int(written)
            status["written_bytes"] = wb
            status["written_human"] = format_bytes_human(wb)
        except (TypeError, ValueError):
            pass

    elapsed = po.get("elapsed_seconds") if po.get("elapsed_seconds") is not None else po.get("running_for_s")
    if elapsed is not None:
        try:
            status["elapsed_seconds"] = int(elapsed)
        except (TypeError, ValueError):
            pass

    mib_s = po.get("throughput_mib_s")
    if mib_s is not None:
        try:
            rate_bps = float(mib_s) * 1024 * 1024
            status["estimated_write_rate_bytes_per_sec"] = round(rate_bps, 2)
            status["estimated_write_rate_human"] = format_rate_human(rate_bps)
        except (TypeError, ValueError):
            pass

    status["last_progress_at"] = po.get("last_update_at") or _now_iso()

    if last_status_message is not None:
        status["last_status_message"] = last_status_message[:500]
    if last_error_code is not None:
        status["last_error_code"] = last_error_code
    if last_error_message is not None:
        status["last_error_message"] = str(last_error_message)[:500]

    cd = compression_detail if compression_detail is not None else status.get("compression_detail")
    if isinstance(cd, dict):
        engine = cd.get("compression_engine") or cd.get("compression_method")
        if engine:
            status["compression_engine"] = engine
        if "compression_threads" in cd:
            status["compression_threads"] = cd.get("compression_threads")
        if "compression_level" in cd:
            status["compression_level"] = cd.get("compression_level")
        if "compression_available" in cd:
            status["compression_available"] = cd.get("compression_available")
        if cd.get("compression_reason"):
            status["compression_reason"] = cd.get("compression_reason")

    arch = status.get("archive_path")
    if arch:
        status["final_archive_exists"] = bool(status.get("status") == "success" and not status.get("partial_path"))
    partial = status.get("partial_path")
    if partial and status.get("status") not in ("success",):
        try:
            from pathlib import Path

            status["final_archive_exists"] = Path(str(arch or "")).is_file() if arch else False
        except OSError:
            status["final_archive_exists"] = False

    ns = status.get("notification_email_status")
    if ns:
        status["notification_status"] = ns
