"""Runtime snapshot fragments for /api/version and diagnostics."""

from __future__ import annotations

from typing import Any

from runtime_governance.models import RuntimeCapabilities, RuntimeGovernanceBundle, RuntimeSnapshotParts


def capabilities_to_profile_api_dict(
    bundle: RuntimeGovernanceBundle,
) -> dict[str, Any]:
    cap = bundle.capabilities
    prof = bundle.profile
    return {
        "install_profile": prof.name,
        "raw_install_profile": prof.raw_value,
        "app_edition": bundle.app_edition,
        "manifest_profile": prof.name,
        "dev_control_enabled": cap.dev_control_enabled,
        "dev_diagnostics_enabled": cap.dev_diagnostics_enabled,
        "fleet_sessions_enabled": cap.fleet_sessions_enabled,
        "rescue_remote_enabled": cap.rescue_remote_enabled,
        "write_runbooks_enabled": cap.write_runbooks_enabled,
        "dev_server_enabled": cap.dev_server_enabled,
        "public_exposure_allowed": cap.public_exposure_allowed,
        "profile_source": prof.source,
        "profile_errors": list(cap.profile_errors),
        "profile_warnings": list(cap.profile_warnings),
    }


def build_profile_gate_audit(
    bundle: RuntimeGovernanceBundle,
    route_paths: list[str],
    *,
    http_accessible_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    """Audit API visibility vs active profile (delegates to legacy audit for parity)."""
    from core.install_profile import profile_gate_audit_route_paths
    from runtime_governance.service import materialize_install_profile_state

    state = materialize_install_profile_state()
    return profile_gate_audit_route_paths(
        route_paths,
        http_accessible_prefixes=http_accessible_prefixes,
    )


def build_runtime_ports_fields(
    bundle: RuntimeGovernanceBundle,
) -> dict[str, Any]:
    from core.runtime_ports import version_api_port_fields

    cap = bundle.capabilities
    return version_api_port_fields(
        install_profile=bundle.profile.name,
        dev_control_enabled=cap.dev_control_enabled,
    )


def build_runtime_snapshot_parts(
    bundle: RuntimeGovernanceBundle,
    route_paths: list[str],
) -> RuntimeSnapshotParts:
    return RuntimeSnapshotParts(
        profile_api_dict=capabilities_to_profile_api_dict(bundle),
        profile_gate_audit=build_profile_gate_audit(bundle, route_paths),
        runtime_ports_fields=build_runtime_ports_fields(bundle),
        dev_control_enabled=bundle.capabilities.dev_control_enabled,
        install_profile=bundle.profile.name,
    )
