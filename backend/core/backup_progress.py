"""Strukturiertes progress_optional für Backup-Jobs (Runner / API)."""

from __future__ import annotations

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def merge_progress_optional(
    existing: dict[str, Any] | None,
    *,
    phase: str,
    bytes_current: int,
    bytes_total_estimate: int | None,
    start_monotonic: float,
    compression_method: str,
    current_operation: str,
    target_mount: str | None,
    target_free_bytes: int | None,
    warning_codes: list[str] | None,
    health_flags: dict[str, Any] | None,
    throughput_state: dict[str, Any],
) -> dict[str, Any]:
    now_m = time.monotonic()
    elapsed = max(0.0, now_m - start_monotonic)
    prev_b = int(throughput_state.get("last_bytes") or 0)
    prev_t = float(throughput_state.get("last_t") or start_monotonic)
    mib_s: float | None = None
    if bytes_current > prev_b and now_m > prev_t + 0.5:
        delta_b = bytes_current - prev_b
        delta_t = now_m - prev_t
        if delta_t > 0:
            mib_s = (delta_b / delta_t) / (1024 * 1024)
        throughput_state["last_bytes"] = bytes_current
        throughput_state["last_t"] = now_m

    eta: int | None = None
    if bytes_total_estimate is not None and bytes_total_estimate > 0 and mib_s and mib_s > 0.001:
        remaining = max(0, bytes_total_estimate - bytes_current)
        eta = int(remaining / (mib_s * 1024 * 1024))

    from core.backup_telemetry import format_bytes_human, format_rate_human

    base = dict(existing) if isinstance(existing, dict) else {}
    rate_bps = (float(mib_s) * 1024 * 1024) if mib_s is not None else None
    out: dict[str, Any] = {
        **base,
        "phase": phase,
        "bytes_current": bytes_current,
        "written_human": format_bytes_human(bytes_current),
        "bytes_total_estimate": bytes_total_estimate,
        "elapsed_seconds": int(elapsed),
        "throughput_mib_s": round(mib_s, 4) if mib_s is not None else None,
        "estimated_write_rate_bytes_per_sec": round(rate_bps, 2) if rate_bps else None,
        "estimated_write_rate_human": format_rate_human(rate_bps),
        "compression_method": compression_method,
        "compression_engine": compression_method,
        "current_operation": current_operation,
        "target_mount": target_mount,
        "target_free_bytes": target_free_bytes,
        "last_update_at": _now_iso(),
        "warning_codes": list(warning_codes or []),
        "health_flags": dict(health_flags or {}),
    }
    return out


def quick_target_preflight(backup_dir: str) -> dict[str, Any]:
    """Nur lesend: freier Speicher am Ziel, Mount-Pfad."""
    out: dict[str, Any] = {
        "target_free_bytes": None,
        "target_mount": None,
        "preflight_notes": [],
    }
    try:
        p = Path(backup_dir).resolve()
        out["target_free_bytes"] = int(shutil.disk_usage(p).free)
        out["target_mount"] = str(p)
    except OSError as e:
        out["preflight_notes"].append(f"path_error:{e}")
    return out
