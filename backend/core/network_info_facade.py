"""
Network Info Facade — canonical read-only network discovery for HTTP routes.

Phase G.2: contract + delegation only; routes unchanged.
Delegates to ``core.network_discovery`` (G.8). No network writes, no nmcli/ip link mutations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from core.dcc_status_facade import build_section_status
from core.network_discovery import (
    detect_frontend_port,
    discover_demo_network,
    discover_network_info,
)

FACADE_VERSION = 1

FACADE_STATUS_VALUES = frozenset(
    {
        "ok",
        "warning",
        "degraded",
        "blocked",
        "unavailable",
        "unknown",
    }
)

NETWORK_INFO_KEYS = frozenset(
    {
        "ips",
        "localhost",
        "primary_ip",
        "interfaces",
        "warnings",
        "source",
        "hostname",
    }
)


@dataclass(frozen=True)
class NetworkInfoFacadeWarning:
    code: str
    message: str
    section: str | None = None


@dataclass
class NetworkInfoSection:
    section_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class NetworkInfoFacadeResult:
    facade_version: int = FACADE_VERSION
    sections: list[NetworkInfoSection] = field(default_factory=list)
    warnings: list[NetworkInfoFacadeWarning] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def normalize_legacy_network_info(info: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize legacy network info dict; preserve known keys unchanged."""
    body = info if isinstance(info, dict) else {}
    ips = body.get("ips") if isinstance(body.get("ips"), list) else []
    warnings = body.get("warnings") if isinstance(body.get("warnings"), list) else []
    source = str(body.get("source") or "none")
    if ips:
        status = "ok"
    elif warnings:
        status = "warning"
    elif source == "demo":
        status = "ok"
    else:
        status = "unavailable"
    normalized = {k: body.get(k) for k in NETWORK_INFO_KEYS if k in body}
    return {
        "status": build_section_status(status),
        "legacy_status": status,
        "source": source,
        "ip_count": len(ips),
        "warning_count": len(warnings),
        "normalized": normalized,
        "legacy": body,
    }


def build_unavailable_network_section(section_id: str, *, reason: str) -> NetworkInfoSection:
    return NetworkInfoSection(
        section_id=section_id,
        status="unavailable",
        data={},
        errors=[reason],
        warnings=[reason],
    )


def _warning(code: str, message: str, section: str | None = None) -> NetworkInfoFacadeWarning:
    return NetworkInfoFacadeWarning(code=code, message=message, section=section)


def _safe_section(
    section_id: str,
    builder: Callable[[], NetworkInfoSection],
    *,
    facade_warnings: list[NetworkInfoFacadeWarning],
    facade_errors: list[str],
) -> NetworkInfoSection:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001
        msg = f"{section_id}_failed:{exc}"
        facade_errors.append(msg)
        facade_warnings.append(_warning(f"{section_id}_unavailable", msg, section_id))
        return build_unavailable_network_section(section_id, reason=msg)


def build_network_info() -> dict[str, Any]:
    """Canonical network info payload (legacy ``get_network_info`` shape)."""
    info = discover_network_info()
    return info if isinstance(info, dict) else {}


def build_demo_network_info() -> dict[str, Any]:
    """Demo network placeholder (legacy ``_demo_network`` shape)."""
    info = discover_demo_network()
    return info if isinstance(info, dict) else {}


def build_api_status_payload(*, use_demo: bool = False) -> dict[str, Any]:
    """Legacy ``GET /api/status`` payload (G.4)."""
    net = build_demo_network_info() if use_demo else build_network_info()
    return {
        "status": "healthy",
        "hostname": net["hostname"],
        "version": "1.0.0",
        "network": net,
    }


def build_system_network_response(*, use_demo: bool = False) -> dict[str, Any]:
    """Legacy ``GET /api/system/network`` success payload (G.2b)."""
    if use_demo:
        demo = build_demo_network_info()
        demo_ips = demo.get("ips", []) if isinstance(demo, dict) else []
        return {
            "status": "success",
            "ips": demo_ips,
            "localhost": "127.0.0.1",
            "primary_ip": demo_ips[0] if demo_ips else None,
            "interfaces": [{"name": "demo0", "ip": ip, "source": "demo"} for ip in demo_ips],
            "warnings": [],
            "source": "demo",
            "hostname": demo.get("hostname", "demo-host") if isinstance(demo, dict) else "demo-host",
            "frontend_port": 3001,
            "backend_port": 8000,
        }
    net_info = build_network_info()
    frontend_port = detect_frontend_port()
    return {
        "status": "success",
        "ips": net_info.get("ips", []),
        "localhost": net_info.get("localhost", "127.0.0.1"),
        "primary_ip": net_info.get("primary_ip"),
        "interfaces": net_info.get("interfaces", []),
        "warnings": net_info.get("warnings", []),
        "source": net_info.get("source", "none"),
        "hostname": net_info.get("hostname", "unknown"),
        "frontend_port": frontend_port,
        "backend_port": 8000,
    }


def build_network_status_section(*, use_demo: bool = False) -> dict[str, Any]:
    """Network status section wrapping legacy info (read-only)."""
    warnings: list[NetworkInfoFacadeWarning] = []
    errors: list[str] = []

    def _build() -> NetworkInfoSection:
        info = build_demo_network_info() if use_demo else build_network_info()
        normalized = normalize_legacy_network_info(info)
        section_warnings = [str(w) for w in (info.get("warnings") or []) if str(w).strip()]
        return NetworkInfoSection(
            section_id="network",
            status=str(normalized.get("status") or "unknown"),
            data={"info": info, "normalized": normalized},
            warnings=section_warnings,
        )

    section = _safe_section("network", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_network_info_diagnostics() -> dict[str, Any]:
    """Lightweight facade diagnostics — no active network probe."""
    return {
        "facade_version": FACADE_VERSION,
        "facade_module": "core.network_info_facade",
        "status_vocabulary": sorted(FACADE_STATUS_VALUES),
        "legacy_info_keys": sorted(NETWORK_INFO_KEYS),
        "delegates_to": [
            "network_discovery.discover_network_info",
            "network_discovery.discover_demo_network",
            "network_discovery.detect_frontend_port",
            "app._is_demo_mode",
        ],
        "public_functions": [
            "build_network_info",
            "build_network_status_section",
            "build_demo_network_info",
            "detect_frontend_port",
            "build_api_status_payload",
            "build_system_network_response",
            "build_network_info_diagnostics",
            "normalize_legacy_network_info",
            "build_unavailable_network_section",
        ],
        "routes_migrated_to_facade": [
            "GET /api/status",
            "GET /api/system/network",
            "GET /api/system-info",
            "GET /api/webserver/status",
        ],
        "routes_extracted_to_network_router": [
            "GET /api/status",
            "GET /api/system/network",
        ],
        "network_router_module": "api.routes.network",
        "read_only": True,
        "writes_allowed": False,
        "network_writes_allowed": False,
        "rescue_diagnostics_relevant": True,
    }
