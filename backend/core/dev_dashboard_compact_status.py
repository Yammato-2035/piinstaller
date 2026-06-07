"""Compact DCC status — small operator-facing summary without full dashboard payload."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from core.install_profile import get_install_profile_state
from core.rescue_network_telemetry_gate import build_compact_network_telemetry_status
from core.rescue_telemetry_ingest import build_health_payload
from core.rescue_telemetry_lan_proxy import build_compact_telemetry_lan_proxy_status


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
        try:
            if p.is_dir():
                return {"detected": True, "mount_path": raw, "source": "filesystem"}
        except OSError:
            continue
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

    usb_operator: dict[str, Any] = {}
    try:
        from core.rescue_fat32_esp_usb_writer import build_compact_usb_writer_modes_summary
        from core.rescue_usb_operator_selection import (
            build_compact_usb_operator_summary,
            build_operator_gate_blockers,
            load_operator_selection_evidence,
        )

        usb_operator = build_compact_usb_operator_summary()
        usb_writer_modes = build_compact_usb_writer_modes_summary()
        usb_operator["usb_writer_modes"] = usb_writer_modes
        evidence = load_operator_selection_evidence()
        for code in build_operator_gate_blockers(evidence):
            if code not in blockers:
                blockers.append(code)
    except Exception:
        usb_operator = {"usb_detected": False, "operator_selection_present": False, "destructive_write_allowed": False}
        usb_writer_modes = {}

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

    dev_server: dict[str, Any] = {"enabled": False, "mode": "disabled", "host_locally_allowed": False}
    try:
        from core.developer_capability import is_dev_server_host_locally_allowed
        from devserver.config import load_dev_server_config

        cfg = load_dev_server_config()
        host_allowed = is_dev_server_host_locally_allowed(
            install_profile=state.install_profile,
            dev_control_enabled=state.dev_control_enabled,
        )
        dev_server = {
            "enabled": bool(cfg.enabled),
            "mode": str(cfg.mode or "disabled"),
            "host_locally_allowed": host_allowed,
            "routes_available": bool(cfg.enabled or host_allowed),
            "require_token": bool(cfg.require_token),
        }
    except Exception:
        pass

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
        "dev_server": dev_server,
        "rescue": {
            "iso_uefi_validated": gate.get("uefi_boot_ready") is True and gate.get("iso_verified") is True,
            "iso_sha256_prefix": str(gate.get("iso_sha256") or "")[:16] or None,
            "usb_written": gate.get("usb_stick_written"),
            "usb_mount_detected": usb_mount.get("detected"),
            "usb_mount_path": usb_mount.get("mount_path"),
            "target_boot_validated": gate.get("target_laptop_booted_from_stick") is True,
            "start_assistant_autostart_validated": gate.get("start_assistant_autostart_validated") is True,
            "target_network_telemetry_validated": gate.get("target_network_telemetry_validated") is True,
            "windows_inspect_executable": gate.get("windows_inspect_executable") is True,
            "usb_operator": usb_operator,
            "usb_writer_modes": usb_operator.get("usb_writer_modes") or {},
            "telemetry_lan_proxy": build_compact_telemetry_lan_proxy_status(),
            "network_telemetry": build_compact_network_telemetry_status(),
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
