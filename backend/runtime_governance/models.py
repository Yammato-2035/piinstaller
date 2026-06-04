"""Typed models for runtime governance decisions (no FastAPI, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    source: str
    raw_value: str | None


@dataclass(frozen=True)
class RuntimeCapabilities:
    dev_control_enabled: bool
    dev_diagnostics_enabled: bool
    fleet_sessions_enabled: bool
    rescue_remote_enabled: bool
    write_runbooks_enabled: bool
    dev_server_enabled: bool
    public_exposure_allowed: bool
    profile_errors: tuple[str, ...] = ()
    profile_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DevServerPolicy:
    """Env defaults when explicit SETUPHELFER_DEV_SERVER_* vars are unset."""

    enabled_default: bool | None
    mode_default: str | None
    require_token_default: bool | None


@dataclass(frozen=True)
class RouteExposureDecision:
    allowed: bool
    block_code: str | None = None


@dataclass(frozen=True)
class RuntimeSnapshotParts:
    """Fields merged into /api/version (profile, gate, ports)."""

    profile_api_dict: dict[str, Any]
    profile_gate_audit: dict[str, Any]
    runtime_ports_fields: dict[str, Any]
    dev_control_enabled: bool
    install_profile: str


@dataclass(frozen=True)
class RuntimeGovernanceBundle:
    profile: RuntimeProfile
    capabilities: RuntimeCapabilities
    app_edition: str
