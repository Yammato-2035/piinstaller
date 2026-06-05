"""HTTP route exposure decisions from runtime capabilities."""

from __future__ import annotations

from runtime_governance.models import RouteExposureDecision, RuntimeCapabilities


RESCUE_TELEMETRY_API_PREFIX = "/api/rescue/telemetry"


def decide_route_exposure(path: str, capabilities: RuntimeCapabilities) -> RouteExposureDecision:
    p = path.split("?")[0].rstrip("/") or "/"
    if p.startswith(RESCUE_TELEMETRY_API_PREFIX):
        return RouteExposureDecision(True, None)
    if p.startswith("/api/fleet") and not capabilities.fleet_sessions_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/rescue-agent") and not capabilities.rescue_remote_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/dev-diagnostics") and not capabilities.dev_diagnostics_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/rescue-remote") and not capabilities.rescue_remote_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/dev-dashboard") and not capabilities.dev_control_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/dev-server") and not capabilities.dev_server_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    return RouteExposureDecision(True, None)


def should_register_fleet_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.fleet_sessions_enabled


def should_register_dev_diagnostics_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.dev_diagnostics_enabled


def should_register_rescue_remote_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.rescue_remote_enabled and not capabilities.write_runbooks_enabled


def should_register_rescue_agent_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.rescue_remote_enabled and not capabilities.write_runbooks_enabled


def should_register_dev_server_router(capabilities: RuntimeCapabilities) -> bool:
    return capabilities.dev_server_enabled
