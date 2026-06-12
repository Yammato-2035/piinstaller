"""
Version API route (Phase E.1).

Read-only /api/version extracted from app.py — uses existing core/runtime_governance helpers.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app_bootstrap.version_router_diagnostics import inject_router_diagnostics

router = APIRouter(tags=["version"])


@router.get("/api/version")
async def get_version(request: Request):
    """Gibt zentrale Projektversion, Stage, Track und Laufzeit-Metadaten zurück (Versions-Gate)."""
    from app import get_app_edition
    from core.install_paths import get_backend_runtime_dir, get_install_profile
    from core.install_profile import audit_frontend_backend_profile
    from core.liveness import build_version_api_payload
    from core.profile_deploy_manifest import manifest_sha256, profile_manifest_path
    from runtime_governance.service import (
        build_runtime_snapshot_parts,
        materialize_install_profile_state,
        resolve_runtime_governance_bundle,
    )

    runtime_path = str(get_backend_runtime_dir().resolve())
    bundle = resolve_runtime_governance_bundle()
    state = materialize_install_profile_state()
    built = build_version_api_payload(
        runtime_path=runtime_path,
        install_profile=get_install_profile(),
        app_edition=get_app_edition(),
    )
    if built.get("_error"):
        body = built["body"]
        return JSONResponse(status_code=int(built.get("status_code") or 503), content=body)
    body = dict(built["body"])
    body["runtime_install_location"] = get_install_profile()
    route_paths = [
        getattr(r, "path", "")
        for r in request.app.routes
        if getattr(r, "path", None)
    ]
    snapshot = build_runtime_snapshot_parts(bundle, route_paths)
    body.update(snapshot.profile_api_dict)
    body.update(snapshot.profile_gate_audit)
    body["dev_control_enabled"] = snapshot.dev_control_enabled
    body.update(snapshot.runtime_ports_fields)
    mpath = profile_manifest_path(state.manifest_profile)
    body["runtime_manifest_sha256"] = manifest_sha256(mpath)
    fe_profile = (os.environ.get("SETUPHELFER_FRONTEND_BUILD_PROFILE") or "").strip()
    body["frontend_build_profile"] = fe_profile or state.install_profile
    body["frontend_build_id"] = (os.environ.get("SETUPHELFER_BUILD_ID") or "").strip() or None
    body.update(
        audit_frontend_backend_profile(
            frontend_build_profile=body["frontend_build_profile"],
            backend_profile=state.install_profile,
        )
    )
    if body.get("frontend_profile_mismatch") and body.get("profile_gate_status") != "red":
        body["profile_gate_status"] = "red"
        errs = list(body.get("profile_gate_errors") or [])
        errs.extend(body.get("frontend_profile_audit_errors") or [])
        body["profile_gate_errors"] = errs
    from core.developer_capability import developer_capability_status_for_api

    body.update(
        developer_capability_status_for_api(
            install_profile=state.install_profile,
            dev_control_enabled=state.dev_control_enabled,
        )
    )
    return inject_router_diagnostics(body)
