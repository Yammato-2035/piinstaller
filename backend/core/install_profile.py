"""
Installationsprofile: steuern welche Dev-/Lab-Komponenten aktiv sind.

Code darf im Repo liegen; Aktivierung nur über Profil + Capability-Gates.
Default: release (keine Dev-Routen).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

VALID_PROFILES = frozenset({"release", "developer", "local_lab", "rescue_lab", "production"})

FORBIDDEN_API_PREFIXES_RELEASE = (
    "/api/fleet",
    "/api/dev-diagnostics",
    "/api/rescue-remote",
    "/api/dev-dashboard",
    "/api/dev-server",
)

REQUIRED_API_PREFIXES_LOCAL_LAB = (
    "/api/fleet",
    "/api/dev-diagnostics",
    "/api/dev-dashboard",
)


@dataclass(frozen=True)
class InstallProfileState:
    install_profile: str
    app_edition: str
    dev_control_enabled: bool
    dev_diagnostics_enabled: bool
    fleet_sessions_enabled: bool
    rescue_remote_enabled: bool
    write_runbooks_enabled: bool
    dev_server_enabled: bool
    public_exposure_allowed: bool
    manifest_profile: str
    profile_source: str
    profile_errors: tuple[str, ...] = ()
    profile_warnings: tuple[str, ...] = ()


def _env_truthy(key: str) -> bool:
    return (os.environ.get(key) or "").strip().lower() in ("1", "true", "yes", "on")


def _resolve_profile_name() -> tuple[str, str]:
    raw = (os.environ.get("SETUPHELFER_INSTALL_PROFILE") or "").strip().lower()
    source = "env"
    if raw in VALID_PROFILES:
        return raw, source
    if _env_truthy("PI_INSTALLER_DEV"):
        return "developer", "pi_installer_dev"
    return "release", "default"


def _capabilities_for_profile(name: str) -> dict[str, bool]:
    if name == "release":
        return {
            "dev_control_enabled": False,
            "dev_diagnostics_enabled": False,
            "fleet_sessions_enabled": False,
            "rescue_remote_enabled": False,
            "write_runbooks_enabled": False,
            "dev_server_enabled": False,
            "public_exposure_allowed": False,
        }
    if name == "developer":
        return {
            "dev_control_enabled": True,
            "dev_diagnostics_enabled": True,
            "fleet_sessions_enabled": True,
            "rescue_remote_enabled": False,
            "write_runbooks_enabled": False,
            "dev_server_enabled": True,
            "public_exposure_allowed": False,
        }
    if name == "local_lab":
        return {
            "dev_control_enabled": True,
            "dev_diagnostics_enabled": True,
            "fleet_sessions_enabled": True,
            "rescue_remote_enabled": True,
            "write_runbooks_enabled": False,
            "dev_server_enabled": True,
            "public_exposure_allowed": False,
        }
    if name == "rescue_lab":
        return {
            "dev_control_enabled": False,
            "dev_diagnostics_enabled": True,
            "fleet_sessions_enabled": True,
            "rescue_remote_enabled": True,
            "write_runbooks_enabled": False,
            "dev_server_enabled": True,
            "public_exposure_allowed": False,
        }
    if name == "production":
        return {
            "dev_control_enabled": False,
            "dev_diagnostics_enabled": False,
            "fleet_sessions_enabled": False,
            "rescue_remote_enabled": False,
            "write_runbooks_enabled": False,
            "dev_server_enabled": False,
            "public_exposure_allowed": False,
        }
    return _capabilities_for_profile("release")


def get_install_profile_state() -> InstallProfileState:
    name, source = _resolve_profile_name()
    caps = _capabilities_for_profile(name)
    errors: list[str] = []
    warnings: list[str] = []

    if name not in VALID_PROFILES:
        errors.append(f"invalid_install_profile:{name}")
        name = "release"
        caps = _capabilities_for_profile("release")

    caps = dict(caps)
    env_overrides = (
        ("dev_control_enabled", "SETUPHELFER_DEV_CONTROL_ENABLED"),
        ("dev_diagnostics_enabled", "SETUPHELFER_DEV_DIAGNOSTICS_ENABLED"),
        ("fleet_sessions_enabled", "SETUPHELFER_FLEET_SESSIONS_ENABLED"),
        ("rescue_remote_enabled", "SETUPHELFER_RESCUE_REMOTE_ENABLED"),
        ("dev_server_enabled", "SETUPHELFER_DEV_SERVER_ENABLED"),
    )
    for flag, env_key in env_overrides:
        if _env_truthy(env_key):
            caps[flag] = True

    if _env_truthy("SETUPHELFER_PUBLIC_EXPOSURE_ALLOWED"):
        if not _env_truthy("SETUPHELFER_OPERATOR_CONFIRM_PUBLIC_BIND"):
            errors.append("public_exposure_requires_operator_confirm")
            caps = {**caps, "public_exposure_allowed": False}
        else:
            caps = {**caps, "public_exposure_allowed": True}

    caps["write_runbooks_enabled"] = False  # Phase 1 hard block

    if caps.get("public_exposure_allowed"):
        warnings.append("public_exposure_only_with_operator_confirm")

    edition = (os.environ.get("APP_EDITION") or "release").strip().lower()
    if edition not in ("repo", "release"):
        edition = "release"

    return InstallProfileState(
        install_profile=name,
        app_edition=edition,
        manifest_profile=name,
        profile_source=source,
        profile_errors=tuple(errors),
        profile_warnings=tuple(warnings),
        **caps,
    )


def path_allowed_for_active_profile(path: str) -> bool:
    """HTTP gate: block Dev/Lab API prefixes when capability off."""
    p = path.split("?")[0].rstrip("/") or "/"
    state = get_install_profile_state()
    if p.startswith("/api/fleet") and not state.fleet_sessions_enabled:
        return False
    if p.startswith("/api/dev-diagnostics") and not state.dev_diagnostics_enabled:
        return False
    if p.startswith("/api/rescue-remote") and not state.rescue_remote_enabled:
        return False
    if p.startswith("/api/dev-dashboard") and not state.dev_control_enabled:
        return False
    if p.startswith("/api/dev-server") and not state.dev_server_enabled:
        return False
    return True


def should_register_fleet_router() -> bool:
    return get_install_profile_state().fleet_sessions_enabled


def should_register_dev_diagnostics_router() -> bool:
    return get_install_profile_state().dev_diagnostics_enabled


def should_register_rescue_remote_router() -> bool:
    st = get_install_profile_state()
    return st.rescue_remote_enabled and not st.write_runbooks_enabled


def should_register_dev_server_router() -> bool:
    return get_install_profile_state().dev_server_enabled


def profile_gate_audit_route_paths(route_paths: list[str]) -> dict[str, Any]:
    """Audit registered FastAPI paths vs active profile."""
    state = get_install_profile_state()
    errors: list[str] = []
    warnings: list[str] = []
    paths = sorted({p for p in route_paths if p})

    def _any(prefix: str) -> bool:
        return any(p == prefix or p.startswith(prefix + "/") for p in paths)

    if state.install_profile in ("release", "production"):
        for prefix in FORBIDDEN_API_PREFIXES_RELEASE:
            if _any(prefix):
                errors.append(f"release_profile_dev_routes_visible:{prefix}")
    if state.install_profile == "local_lab":
        for prefix in REQUIRED_API_PREFIXES_LOCAL_LAB:
            if not _any(prefix):
                warnings.append(f"required_api_path_missing:{prefix}")

    status = "green"
    if errors:
        status = "red"
    elif warnings:
        status = "yellow"

    return {
        "profile_gate_status": status,
        "profile_gate_errors": errors,
        "profile_gate_warnings": warnings,
        "forbidden_api_paths_registered": [
            p for p in paths
            if any(p.startswith(x) for x in FORBIDDEN_API_PREFIXES_RELEASE)
        ],
    }


def audit_frontend_backend_profile(
    *,
    frontend_build_profile: str | None,
    backend_profile: str | None,
) -> dict[str, Any]:
    """Compare frontend build profile marker vs backend capability profile."""
    fe = (frontend_build_profile or "").strip().lower()
    be = (backend_profile or "").strip().lower()
    mismatch = False
    warnings: list[str] = []
    errors: list[str] = []
    if not fe:
        return {
            "frontend_profile_mismatch": False,
            "frontend_profile_audit_warnings": ["frontend_build_profile_unknown"],
        }
    if fe == be:
        return {"frontend_profile_mismatch": False, "frontend_profile_audit_warnings": warnings}
    release_like = frozenset({"release", "production"})
    lab_like = frozenset({"developer", "local_lab", "rescue_lab"})
    if be in release_like and fe in lab_like:
        mismatch = True
        errors.append("frontend_profile_mismatch:backend_release_frontend_lab")
    elif be in lab_like and fe in release_like:
        mismatch = True
        warnings.append("frontend_profile_mismatch:backend_lab_frontend_release")
    elif fe != be:
        warnings.append(f"frontend_profile_mismatch:{fe}!={be}")
    return {
        "frontend_profile_mismatch": mismatch,
        "frontend_profile_audit_errors": errors,
        "frontend_profile_audit_warnings": warnings,
    }


def profile_state_to_api_dict(state: InstallProfileState | None = None) -> dict[str, Any]:
    st = state or get_install_profile_state()
    return {
        "install_profile": st.install_profile,
        "app_edition": st.app_edition,
        "manifest_profile": st.manifest_profile,
        "dev_control_enabled": st.dev_control_enabled,
        "dev_diagnostics_enabled": st.dev_diagnostics_enabled,
        "fleet_sessions_enabled": st.fleet_sessions_enabled,
        "rescue_remote_enabled": st.rescue_remote_enabled,
        "write_runbooks_enabled": st.write_runbooks_enabled,
        "dev_server_enabled": st.dev_server_enabled,
        "public_exposure_allowed": st.public_exposure_allowed,
        "profile_source": st.profile_source,
        "profile_errors": list(st.profile_errors),
        "profile_warnings": list(st.profile_warnings),
    }
