"""
Network Info Facade — canonical read-only network discovery for HTTP routes.

Phase G.2: contract + delegation only; routes unchanged.
Delegates to existing ``app.get_network_info`` / ``app._demo_network``.
No network writes, no nmcli/ip link mutations, no new discovery logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from core.dcc_status_facade import build_section_status

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


def _legacy_get_network_info() -> dict[str, Any]:
    """Legacy adapter: discovery still lives in ``app.get_network_info`` (G.2b)."""
    import app as app_module

    info = app_module.get_network_info()
    return info if isinstance(info, dict) else {}


def _legacy_demo_network() -> dict[str, Any]:
    """Legacy adapter: demo placeholder still lives in ``app._demo_network``."""
    import app as app_module

    info = app_module._demo_network()
    return info if isinstance(info, dict) else {}


def build_network_info() -> dict[str, Any]:
    """Canonical network info payload (legacy ``get_network_info`` shape)."""
    return _legacy_get_network_info()


def build_demo_network_info() -> dict[str, Any]:
    """Demo network placeholder (legacy ``_demo_network`` shape)."""
    return _legacy_demo_network()


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
            "app.get_network_info",
            "app._demo_network",
            "app._is_demo_mode",
            "app._detect_frontend_port",
        ],
        "public_functions": [
            "build_network_info",
            "build_network_status_section",
            "build_demo_network_info",
            "build_network_info_diagnostics",
            "normalize_legacy_network_info",
            "build_unavailable_network_section",
        ],
        "routes_pending_facade_migration": [
            "GET /api/status",
            "GET /api/system/network",
        ],
        "read_only": True,
        "writes_allowed": False,
        "network_writes_allowed": False,
        "rescue_diagnostics_relevant": True,
    }
