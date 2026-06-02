from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Callable

from core.install_profile import get_install_profile_state


def build_dcc_profile_block_response() -> dict[str, Any] | None:
    state = get_install_profile_state()
    if not state.dev_control_enabled:
        return {
            "status": "error",
            "code": "PROFILE_ROUTE_BLOCKED",
            "profile": state.install_profile,
            "message": "Development Dashboard is blocked in release profile",
            "required_profile": "local_lab",
        }
    return None


async def build_dev_dashboard_status(
    *,
    backup_jobs: dict[str, dict[str, Any]],
    sync_stale_runner_job_from_systemd: Callable[[str], None],
    job_snapshot: Callable[[dict[str, Any]], dict[str, Any]],
    detect_active_package_operations: Callable[[], dict[str, Any]],
    frontend_build_version: str | None,
    frontend_runtime_source: str | None,
) -> dict[str, Any]:
    from core import dev_dashboard as dev_dashboard_core

    blocked = build_dcc_profile_block_response()
    if blocked:
        return blocked

    def _build_sync() -> dict[str, Any]:
        for jid in list(backup_jobs.keys())[:32]:
            sync_stale_runner_job_from_systemd(jid)
        running: list[dict[str, Any]] = []
        for _job_id, job in backup_jobs.items():
            status = job.get("status", "")
            if status in ("queued", "running", "cancel_requested") or not status:
                running.append(job_snapshot(job))
        pkg = detect_active_package_operations()
        fe_ver = (frontend_build_version or "").strip() or None
        return dev_dashboard_core.build_dashboard_status(
            running_jobs=running,
            package_activity=pkg,
            frontend_build_version=fe_ver,
            frontend_runtime_source=frontend_runtime_source,
        )

    total_timeout = float(os.environ.get("SETUPHELFER_DASHBOARD_STATUS_TIMEOUT_SEC", "50"))
    try:
        body = await asyncio.wait_for(asyncio.to_thread(_build_sync), timeout=total_timeout)
        return {"status": "success", "dashboard": body}
    except asyncio.TimeoutError:
        now = datetime.now(timezone.utc).isoformat()
        degraded = {
            "generated_at": now,
            "updated_at": now,
            "backend_running": True,
            "warnings": ["section_timeout_or_unavailable:dashboard_status"],
            "errors": [],
            "deploy_drift": {"status": "gray", "warnings": ["dashboard_status_timeout"]},
            "runtime_gate": {"passed": False, "status": "gray", "warnings": ["dashboard_status_timeout"]},
        }
        return {"status": "degraded", "warning": "dashboard_status_timeout", "dashboard": degraded}

