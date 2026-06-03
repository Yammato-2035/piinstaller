"""
Central runtime port and profile registry (read-only).

Loads config/runtime_ports.json from repo/workspace with embedded fallback.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_EMBEDDED: dict[str, Any] = {
    "version": 1,
    "updated_at": "2026-06-03",
    "ports": {
        "backend_api": {
            "host": "127.0.0.1",
            "port": 8000,
            "base_url": "http://127.0.0.1:8000",
            "purpose": "FastAPI backend and all API routes",
        },
        "frontend_ui": {
            "host": "127.0.0.1",
            "port": 3001,
            "base_url": "http://127.0.0.1:3001",
            "purpose": "SetupHelfer web UI and Development Cockpit window",
        },
        "nginx_default": {
            "host": "127.0.0.1",
            "port": 8080,
            "base_url": "http://127.0.0.1:8080",
            "purpose": "nginx/default site, not SetupHelfer DCC",
        },
        "qemu_lab_proxy_host": {
            "host": "127.0.0.1",
            "port": 8001,
            "base_url": "http://127.0.0.1:8001",
            "purpose": "Host-side QEMU lab proxy to backend API",
        },
        "qemu_guest_devserver": {
            "host": "10.0.2.2",
            "port": 8001,
            "base_url": "http://10.0.2.2:8001",
            "purpose": "Guest-side URL for rescue ISO agent to reach host devserver",
        },
    },
    "profiles": {
        "release": {
            "dev_control_enabled": False,
            "expected_dev_routes": "PROFILE_ROUTE_BLOCKED",
            "public_runtime": True,
            "dcc_ui_available": False,
        },
        "local_lab": {
            "dev_control_enabled": True,
            "expected_dev_routes": "HTTP_200",
            "public_runtime": False,
            "dcc_ui_available": True,
        },
    },
    "canonical_urls": {
        "dcc": "http://127.0.0.1:3001/?window=cockpit",
        "main_ui": "http://127.0.0.1:3001/",
        "api_version": "http://127.0.0.1:8000/api/version",
        "backend_health": "http://127.0.0.1:8000/api/dev-dashboard/backend-health",
        "fleet_sessions": "http://127.0.0.1:8000/api/fleet/sessions",
        "rescue_agent_sessions": "http://127.0.0.1:8000/api/rescue-agent/sessions",
    },
}


def _repo_candidates() -> list[Path]:
    paths: list[Path] = []
    for raw in (
        os.environ.get("SETUPHELFER_REPO_ROOT"),
        os.environ.get("SETUPHELFER_DEV_WORKSPACE_ROOT"),
    ):
        if raw and raw.strip():
            paths.append(Path(raw.strip()))
    try:
        from core import dev_dashboard as dev_dashboard_core

        paths.append(dev_dashboard_core._repo_root())
    except Exception:
        paths.append(Path(__file__).resolve().parent.parent.parent)
    opt = Path("/opt/setuphelfer")
    paths.append(opt)
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def load_runtime_ports_registry(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Return registry dict with source metadata."""
    candidates = [repo_root] if repo_root else []
    candidates.extend(_repo_candidates())
    for root in candidates:
        if root is None:
            continue
        path = Path(root) / "config" / "runtime_ports.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("ports"):
                return {
                    **data,
                    "port_registry_source": str(path.resolve()),
                    "port_registry_fallback": False,
                }
        except (OSError, json.JSONDecodeError):
            continue
    return {
        **_EMBEDDED,
        "port_registry_source": "embedded_defaults",
        "port_registry_fallback": True,
    }


def profile_capabilities_for_install_profile(
    registry: dict[str, Any],
    install_profile: str,
    *,
    dev_control_enabled: bool | None = None,
) -> dict[str, Any]:
    profiles = registry.get("profiles") or {}
    base = dict(profiles.get(install_profile) or profiles.get("release") or {})
    if dev_control_enabled is not None:
        base["dev_control_enabled"] = dev_control_enabled
        base["dcc_ui_available"] = bool(dev_control_enabled)
    return base


def version_api_port_fields(
    *,
    install_profile: str,
    dev_control_enabled: bool,
) -> dict[str, Any]:
    reg = load_runtime_ports_registry()
    return {
        "runtime_ports": reg.get("ports") or {},
        "canonical_urls": reg.get("canonical_urls") or {},
        "profile_capabilities": profile_capabilities_for_install_profile(
            reg,
            install_profile,
            dev_control_enabled=dev_control_enabled,
        ),
        "port_registry_source": reg.get("port_registry_source"),
        "port_registry_fallback": reg.get("port_registry_fallback", False),
    }
