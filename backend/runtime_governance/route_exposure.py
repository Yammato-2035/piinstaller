"""HTTP route exposure decisions from runtime capabilities."""

from __future__ import annotations

from runtime_governance.models import RouteExposureDecision, RuntimeCapabilities


RESCUE_TELEMETRY_API_PREFIX = "/api/rescue/telemetry"
DCC_CAPABILITY_STATUS_PATH = "/api/dev-dashboard/capability-status"
DCC_COMPACT_STATUS_PATH = "/api/dev-dashboard/compact-status"


def _dev_server_host_locally_allowed() -> bool:
    try:
        from core.developer_capability import is_dev_server_host_locally_allowed

        return is_dev_server_host_locally_allowed()
    except Exception:
        return False


def decide_route_exposure(path: str, capabilities: RuntimeCapabilities) -> RouteExposureDecision:
    p = path.split("?")[0].rstrip("/") or "/"
    if p.startswith(RESCUE_TELEMETRY_API_PREFIX):
        return RouteExposureDecision(True, None)
    if p in (DCC_CAPABILITY_STATUS_PATH, DCC_COMPACT_STATUS_PATH):
        return RouteExposureDecision(True, None)
    if p.startswith("/api/fleet") and not capabilities.fleet_sessions_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/rescue-agent") and not capabilities.rescue_remote_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/dev-diagnostics") and not capabilities.dev_diagnostics_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/rescue-remote") and not capabilities.rescue_remote_enabled:
        return RouteExposureDecision(False, "PROFILE_ROUTE_BLOCKED")
    if p.startswith("/api/dev-dashboard"):
        # DCC access is enforced by developer_capability (token + profile), not dev_control alone.
        return RouteExposureDecision(True, None)
    if p.startswith("/api/dev-server") and not capabilities.dev_server_enabled:
        if not _dev_server_host_locally_allowed():
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
    return capabilities.dev_server_enabled or _dev_server_host_locally_allowed()
