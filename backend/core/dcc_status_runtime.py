"""
DCC Status Runtime — job/package adapters for dashboard status facade (Phase E.11).

Isolates ``app`` coupling for ``GET /api/dev-dashboard/status``; routers and facade
must not import ``app`` directly.
"""

from __future__ import annotations

from typing import Any, Callable

DCC_STATUS_RUNTIME_VERSION = 1


def get_dashboard_status_runtime_adapters() -> tuple[
    dict[str, dict[str, Any]],
    Callable[[str], None],
    Callable[[dict[str, Any]], dict[str, Any]],
    Callable[[], dict[str, Any]],
]:
    """Return BACKUP_JOBS registry and legacy sync/snapshot/package probes from app."""
    import app as app_module

    return (
        app_module.BACKUP_JOBS,
        app_module._sync_stale_runner_job_from_systemd,
        app_module._job_snapshot,
        app_module._detect_active_package_operations,
    )
