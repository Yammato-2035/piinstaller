"""Canonical install-profile resolution and capability matrix."""

from __future__ import annotations

import os

from runtime_governance.models import RuntimeCapabilities, RuntimeProfile

VALID_PROFILES = frozenset({"release", "developer", "local_lab", "rescue_lab", "production"})


def _env_truthy(key: str) -> bool:
    return (os.environ.get(key) or "").strip().lower() in ("1", "true", "yes", "on")


def resolve_runtime_profile() -> RuntimeProfile:
    raw = (os.environ.get("SETUPHELFER_INSTALL_PROFILE") or "").strip().lower()
    source = "env"
    raw_value: str | None = raw or None
    if raw == "opt":
        return RuntimeProfile("release", "legacy_profile_opt_mapped_to_release", raw)
    if raw in VALID_PROFILES:
        return RuntimeProfile(raw, source, raw_value)
    if raw:
        return RuntimeProfile("release", "invalid_profile_fallback_release", raw)
    if _env_truthy("PI_INSTALLER_DEV"):
        return RuntimeProfile("developer", "pi_installer_dev", None)
    return RuntimeProfile("release", "default", None)


def build_runtime_capabilities(profile: RuntimeProfile) -> RuntimeCapabilities:
    caps = _base_capabilities_for_profile_name(profile.name)
    errors: list[str] = []
    warnings: list[str] = []

    if profile.source == "legacy_profile_opt_mapped_to_release":
        warnings.append("legacy_profile_opt_mapped_to_release")
    if profile.source == "invalid_profile_fallback_release" and profile.raw_value:
        errors.append(f"invalid_install_profile:{profile.raw_value}")
        warnings.append("invalid_install_profile_fallback_release")

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
            if profile.name in ("release", "production"):
                warnings.append(f"ignored_dev_capability_override_in_release:{env_key}")
            else:
                caps[flag] = True

    if _env_truthy("SETUPHELFER_PUBLIC_EXPOSURE_ALLOWED"):
        if not _env_truthy("SETUPHELFER_OPERATOR_CONFIRM_PUBLIC_BIND"):
            errors.append("public_exposure_requires_operator_confirm")
            caps["public_exposure_allowed"] = False
        else:
            caps["public_exposure_allowed"] = True

    caps["write_runbooks_enabled"] = False

    if caps.get("public_exposure_allowed"):
        warnings.append("public_exposure_only_with_operator_confirm")

    return RuntimeCapabilities(
        profile_errors=tuple(errors),
        profile_warnings=tuple(warnings),
        **caps,
    )


def resolve_app_edition() -> str:
    edition = (os.environ.get("APP_EDITION") or "release").strip().lower()
    if edition not in ("repo", "release"):
        return "release"
    return edition


def _base_capabilities_for_profile_name(name: str) -> dict[str, bool]:
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
    return _base_capabilities_for_profile_name("release")
