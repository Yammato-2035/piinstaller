"""Compact DCC status — small operator-facing summary without full dashboard payload."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from core.install_profile import get_install_profile_state
from core.rescue_telemetry_ingest import build_health_payload


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_rescue_usb_gate() -> dict[str, Any]:
    path = _repo_root() / "docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json"
    if not path.is_file():
        return {"available": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"available": False}
    except (OSError, json.JSONDecodeError):
        return {"available": False}


def _detect_usb_rescue_mount() -> dict[str, Any]:
    candidates = (
        "/media/gabriel/SETUPHELFER_RESCUE",
        "/media/volker/SETUPHELFER_RESCUE",
        "/run/media/gabriel/SETUPHELFER_RESCUE",
        "/run/media/volker/SETUPHELFER_RESCUE",
    )
    for raw in candidates:
        p = Path(raw)
        if p.is_dir():
            return {"detected": True, "mount_path": raw, "source": "filesystem"}
    return {"detected": False, "mount_path": None, "source": "none"}


def _deploy_exposure_summary() -> dict[str, Any]:
    from core.profile_deploy_manifest import enrich_deploy_drift_profile_aware

    route_paths: list[str] = []
    try:
        mod = sys.modules.get("app")
        if mod is not None and hasattr(mod, "app"):
            route_paths = [
                getattr(r, "path", "")
                for r in mod.app.routes
                if getattr(r, "path", None)
            ]
    except Exception:
        pass
    rt = Path("/opt/setuphelfer")
    base = {"status": "green", "suggested_actions": ["none"], "manifest_match": True}
    return enrich_deploy_drift_profile_aware(
        base,
        workspace_root=_repo_root(),
        runtime_root=rt if rt.is_dir() else None,
        route_paths=route_paths,
    )


def build_compact_dcc_status(
    *,
    request_headers: Mapping[str, str] | None = None,
    backend_runtime_path: str,
) -> dict[str, Any]:
    from core.developer_capability import (
        assess_developer_capability,
        build_capability_status_payload,
        is_dcc_route_allowed,
    )

    state = get_install_profile_state()
    capability = build_capability_status_payload(
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        backend_runtime_path=backend_runtime_path,
        request_headers=request_headers,
    )
    assessment = assess_developer_capability(
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        request_headers=request_headers,
    )
    allowed, block_code = is_dcc_route_allowed(
        path="/api/dev-dashboard/status",
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        request_headers=request_headers,
    )

    telemetry = build_health_payload()
    gate = _load_rescue_usb_gate()
    usb_mount = _detect_usb_rescue_mount()
    blockers: list[str] = []
    for item in gate.get("blockers") or []:
        if isinstance(item, dict) and item.get("id"):
            blockers.append(str(item["id"]))

    exposure: dict[str, Any] = {}
    try:
        exposure = _deploy_exposure_summary()
    except Exception:
        exposure = {}

    next_action = (
        gate.get("next_operator_step_de")
        or gate.get("next_operator_step_en")
        or "Rescue-Gate und Deploy-Drift prüfen."
    )

    return {
        "status": "ok",
        "compact": True,
        "install_profile": state.install_profile,
        "dev_control_enabled": state.dev_control_enabled,
        "dcc_visible": bool(capability.get("dcc_visible")),
        "dcc_status_allowed": allowed,
        "dcc_block_code": block_code,
        "developer_capability": {
            "configured": bool(assessment.get("developer_capability_configured")),
            "valid": bool(assessment.get("developer_capability_valid")),
            "reason": capability.get("reason"),
        },
        "deploy_drift_status": str(exposure.get("status") or "unknown"),
        "profile_exposure": exposure.get("profile_exposure") or {},
        "developer_capability_exposure": exposure.get("developer_capability_exposure") or {},
        "telemetry": {
            "health_ok": telemetry.get("status") == "ok",
            "ingest_enabled": bool(telemetry.get("ingest_enabled")),
            "profile_gate_independent": bool(telemetry.get("profile_gate_independent")),
            "last_error_code": telemetry.get("last_error_code"),
        },
        "rescue": {
            "iso_uefi_validated": gate.get("uefi_boot_ready") is True and gate.get("iso_verified") is True,
            "iso_sha256_prefix": str(gate.get("iso_sha256") or "")[:16] or None,
            "usb_written": gate.get("usb_stick_written"),
            "usb_mount_detected": usb_mount.get("detected"),
            "usb_mount_path": usb_mount.get("mount_path"),
            "target_boot_validated": gate.get("target_laptop_booted_from_stick") is True,
            "windows_inspect_executable": gate.get("windows_inspect_executable") is True,
        },
        "blockers": blockers,
        "next_operator_action": str(next_action),
        "details_available": {
            "full_status": "/api/dev-dashboard/status",
            "capability_status": "/api/dev-dashboard/capability-status",
            "telemetry_health": "/api/rescue/telemetry/health",
        },
        "secrets_exposed": False,
    }
