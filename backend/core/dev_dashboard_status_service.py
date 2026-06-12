from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from core.install_profile import get_install_profile_state


def build_dcc_profile_block_response(
    *,
    request_headers: Mapping[str, str] | None = None,
    path: str = "/api/dev-dashboard/status",
) -> dict[str, Any] | None:
    """Return block payload when DCC handler must refuse, else None.

    Uses the same developer capability gate as middleware (not dev_control alone).
    """
    from core.developer_capability import is_dcc_route_allowed

    state = get_install_profile_state()
    allowed, block_code = is_dcc_route_allowed(
        path=path,
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        request_headers=request_headers,
    )
    if allowed:
        return None

    if block_code == "DEVELOPER_CAPABILITY_REQUIRED":
        message = "Valid developer capability token required."
    elif block_code == "DEVELOPER_CAPABILITY_NOT_CONFIGURED":
        message = "Developer capability is not configured on this host."
    else:
        message = "Development Dashboard is blocked for this install profile."

    return {
        "status": "error",
        "code": block_code or "PROFILE_ROUTE_BLOCKED",
        "profile": state.install_profile,
        "message": message,
        "developer_capability_gate": True,
        "rescue_telemetry_separate_from_dcc": True,
    }


async def build_dev_dashboard_status(
    *,
    backup_jobs: dict[str, dict[str, Any]],
    sync_stale_runner_job_from_systemd: Callable[[str], None],
    job_snapshot: Callable[[dict[str, Any]], dict[str, Any]],
    detect_active_package_operations: Callable[[], dict[str, Any]],
    frontend_build_version: str | None,
    frontend_runtime_source: str | None,
    request_headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    blocked = build_dcc_profile_block_response(request_headers=request_headers)
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
        from core.dcc_status_facade import build_dashboard_status_body

        return build_dashboard_status_body(
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
