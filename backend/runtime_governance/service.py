"""Public runtime governance API (no FastAPI, no side effects)."""

from __future__ import annotations

from runtime_governance.devserver_policy import build_devserver_policy
from runtime_governance.models import (
    DevServerPolicy,
    RuntimeGovernanceBundle,
    RuntimeSnapshotParts,
)
from runtime_governance.profile_policy import (
    build_runtime_capabilities,
    resolve_app_edition,
    resolve_runtime_profile,
)
from runtime_governance.route_exposure import decide_route_exposure
from runtime_governance.runtime_snapshot import build_runtime_snapshot_parts


def resolve_runtime_governance_bundle() -> RuntimeGovernanceBundle:
    profile = resolve_runtime_profile()
    capabilities = build_runtime_capabilities(profile)
    return RuntimeGovernanceBundle(
        profile=profile,
        capabilities=capabilities,
        app_edition=resolve_app_edition(),
    )


def materialize_install_profile_state():
    """Build legacy InstallProfileState from canonical governance bundle."""
    from core.install_profile import InstallProfileState

    bundle = resolve_runtime_governance_bundle()
    cap = bundle.capabilities
    prof = bundle.profile
    return InstallProfileState(
        install_profile=prof.name,
        app_edition=bundle.app_edition,
        raw_install_profile=prof.raw_value,
        manifest_profile=prof.name,
        profile_source=prof.source,
        profile_errors=cap.profile_errors,
        profile_warnings=cap.profile_warnings,
        dev_control_enabled=cap.dev_control_enabled,
        dev_diagnostics_enabled=cap.dev_diagnostics_enabled,
        fleet_sessions_enabled=cap.fleet_sessions_enabled,
        rescue_remote_enabled=cap.rescue_remote_enabled,
        write_runbooks_enabled=cap.write_runbooks_enabled,
        dev_server_enabled=cap.dev_server_enabled,
        public_exposure_allowed=cap.public_exposure_allowed,
    )


__all__ = [
    "build_devserver_policy",
    "build_runtime_snapshot_parts",
    "decide_route_exposure",
    "materialize_install_profile_state",
    "resolve_runtime_governance_bundle",
]
