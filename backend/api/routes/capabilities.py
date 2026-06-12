"""
Capability and lightweight DCC gate routes (Phase E.3).

Read-only GET handlers — no shell commands, no storage/safety/mount duplication.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core.install_paths import get_backend_runtime_dir

router = APIRouter(tags=["capabilities"])


@router.get("/api/dev-dashboard/capability-status")
async def dev_dashboard_capability_status(request: Request):
    """Read-only DCC gate diagnosis — no secrets, reachable when DCC routes are blocked."""
    from core.developer_capability import build_capability_status_payload
    from core.install_profile import get_install_profile_state

    state = get_install_profile_state()
    headers = {k: v for k, v in request.headers.items()}
    return build_capability_status_payload(
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        backend_runtime_path=str(get_backend_runtime_dir().resolve()),
        request_headers=headers,
    )


@router.get("/api/dev-dashboard/compact-status")
async def dev_dashboard_compact_status(request: Request):
    """Compact operator summary — no full dashboard payload, no secrets."""
    from core.dev_dashboard_compact_status import build_compact_dcc_status

    headers = {k: v for k, v in request.headers.items()}
    return build_compact_dcc_status(
        request_headers=headers,
        backend_runtime_path=str(get_backend_runtime_dir().resolve()),
    )
