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
    "/api/rescue-agent",
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
    raw_install_profile: str | None
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


def _resolve_profile_name() -> tuple[str, str, str | None]:
    """Return (profile, source, raw_env_value)."""
    raw = (os.environ.get("SETUPHELFER_INSTALL_PROFILE") or "").strip().lower()
    source = "env"
    raw_value: str | None = raw or None
    if raw == "opt":
        return "release", "legacy_profile_opt_mapped_to_release", raw
    if raw in VALID_PROFILES:
        return raw, source, raw_value
    if raw:
        return "release", "invalid_profile_fallback_release", raw
    if _env_truthy("PI_INSTALLER_DEV"):
        return "developer", "pi_installer_dev", None
    return "release", "default", None


def _capabilities_for_profile(name: str) -> dict[str, bool]:
    """Legacy helper — delegates to runtime_governance.profile_policy."""
    from runtime_governance.profile_policy import _base_capabilities_for_profile_name

    return _base_capabilities_for_profile_name(name)


def get_install_profile_state() -> InstallProfileState:
    """Delegates to runtime_governance (canonical policy source)."""
    from runtime_governance.service import materialize_install_profile_state

    return materialize_install_profile_state()


def path_allowed_for_active_profile(path: str) -> bool:
    """HTTP gate: block Dev/Lab API prefixes when capability off."""
    from runtime_governance.route_exposure import decide_route_exposure
    from runtime_governance.service import resolve_runtime_governance_bundle

    bundle = resolve_runtime_governance_bundle()
    return decide_route_exposure(path, bundle.capabilities).allowed


def should_register_fleet_router() -> bool:
    from runtime_governance.route_exposure import should_register_fleet_router as _reg
    from runtime_governance.service import resolve_runtime_governance_bundle

    return _reg(resolve_runtime_governance_bundle().capabilities)


def should_register_dev_diagnostics_router() -> bool:
    from runtime_governance.route_exposure import should_register_dev_diagnostics_router as _reg
    from runtime_governance.service import resolve_runtime_governance_bundle

    return _reg(resolve_runtime_governance_bundle().capabilities)


def should_register_rescue_remote_router() -> bool:
    from runtime_governance.route_exposure import should_register_rescue_remote_router as _reg
    from runtime_governance.service import resolve_runtime_governance_bundle

    return _reg(resolve_runtime_governance_bundle().capabilities)


def should_register_rescue_agent_router() -> bool:
    from runtime_governance.route_exposure import should_register_rescue_agent_router as _reg
    from runtime_governance.service import resolve_runtime_governance_bundle

    return _reg(resolve_runtime_governance_bundle().capabilities)


def should_register_dev_server_router() -> bool:
    from runtime_governance.route_exposure import should_register_dev_server_router as _reg
    from runtime_governance.service import resolve_runtime_governance_bundle

    return _reg(resolve_runtime_governance_bundle().capabilities)


def _capability_enabled_for_prefix(prefix: str, state: InstallProfileState) -> bool:
    if prefix.startswith("/api/fleet"):
        return state.fleet_sessions_enabled
    if prefix.startswith("/api/rescue-agent"):
        return state.rescue_remote_enabled
    if prefix.startswith("/api/dev-diagnostics"):
        return state.dev_diagnostics_enabled
    if prefix.startswith("/api/rescue-remote"):
        return state.rescue_remote_enabled
    if prefix.startswith("/api/dev-dashboard"):
        return state.dev_control_enabled
    if prefix.startswith("/api/dev-server"):
        return state.dev_server_enabled
    return False


def profile_gate_audit_route_paths(
    route_paths: list[str],
    *,
    http_accessible_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    """Audit API visibility vs active profile (capabilities / HTTP, not OpenAPI alone)."""
    state = get_install_profile_state()
    errors: list[str] = []
    warnings: list[str] = []
    paths = sorted({p for p in route_paths if p})
    accessible = sorted({p for p in (http_accessible_prefixes or []) if p})

    def _any_registered(prefix: str) -> bool:
        return any(p == prefix or p.startswith(prefix + "/") for p in paths)

    def _any_accessible(prefix: str) -> bool:
        return any(p == prefix or p.startswith(prefix + "/") for p in accessible)

    if state.install_profile in ("release", "production"):
        for prefix in FORBIDDEN_API_PREFIXES_RELEASE:
            if http_accessible_prefixes is not None:
                if _any_accessible(prefix):
                    errors.append(f"release_profile_dev_routes_accessible:{prefix}")
            elif _capability_enabled_for_prefix(prefix, state) and _any_registered(prefix):
                errors.append(f"release_profile_dev_routes_visible:{prefix}")
    if state.install_profile == "local_lab":
        for prefix in REQUIRED_API_PREFIXES_LOCAL_LAB:
            if http_accessible_prefixes is not None:
                if not _any_accessible(prefix):
                    warnings.append(f"required_api_path_missing:{prefix}")
            elif not _any_registered(prefix):
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
        "raw_install_profile": st.raw_install_profile,
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
