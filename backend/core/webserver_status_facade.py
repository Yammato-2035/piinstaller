"""
Webserver Status Facade — canonical read-only aggregation for GET /api/webserver/status.

Phase G.7: contract + delegation only; route response shape unchanged.
Delegates webserver/service probes to legacy ``app`` helpers.
Network and port via ``network_info_facade`` only — no new discovery logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from core.dcc_status_facade import build_section_status
from core.network_info_facade import build_network_info, detect_frontend_port

WEBSERVER_STATUS_FACADE_VERSION = 1

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


@dataclass(frozen=True)
class WebserverStatusFacadeWarning:
    code: str
    message: str
    section: str | None = None


@dataclass
class WebserverStatusSection:
    section_id: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _warning(code: str, message: str, section: str | None = None) -> WebserverStatusFacadeWarning:
    return WebserverStatusFacadeWarning(code=code, message=message, section=section)


def build_unavailable_webserver_section(section_id: str, *, reason: str) -> WebserverStatusSection:
    return WebserverStatusSection(
        section_id=section_id,
        status="unavailable",
        data={},
        errors=[reason],
        warnings=[reason],
    )


def _safe_section(
    section_id: str,
    builder: Callable[[], WebserverStatusSection],
    *,
    facade_warnings: list[WebserverStatusFacadeWarning],
    facade_errors: list[str],
) -> WebserverStatusSection:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001
        msg = f"{section_id}_failed:{exc}"
        facade_errors.append(msg)
        facade_warnings.append(_warning(f"{section_id}_unavailable", msg, section_id))
        return build_unavailable_webserver_section(section_id, reason=msg)


def _legacy_get_running_services() -> dict[str, bool]:
    import app as app_module

    running = app_module.get_running_services()
    return running if isinstance(running, dict) else {}


def _legacy_get_installed_apps() -> dict[str, Any]:
    import app as app_module

    installed = app_module.get_installed_apps()
    return installed if isinstance(installed, dict) else {}


def _legacy_get_website_names() -> list[str]:
    import app as app_module

    names = app_module.get_website_names()
    return names if isinstance(names, list) else []


def _legacy_run_command(cmd: str) -> dict[str, Any]:
    import app as app_module

    result = app_module.run_command(cmd)
    return result if isinstance(result, dict) else {"success": False, "stdout": "", "stderr": ""}


def _legacy_check_installed(package: str) -> bool:
    import app as app_module

    return bool(app_module.check_installed(package))


def build_webserver_frontend_section(
    *,
    network: dict[str, Any] | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """PI-Installer frontend URL block (legacy ``pi_installer`` shape)."""
    net = network if isinstance(network, dict) else build_network_info()
    pi_installer_port = port if port is not None else detect_frontend_port()
    effective_port = pi_installer_port or 3001
    ips = net.get("ips") if isinstance(net.get("ips"), list) else []
    if ips:
        url = f"http://{ips[0]}:{effective_port}"
    else:
        url = f"http://localhost:{effective_port}"
    return {"port": effective_port, "url": url}


def build_webserver_status() -> dict[str, Any]:
    """Legacy ``GET /api/webserver/status`` payload (G.7)."""
    running = _legacy_get_running_services()
    network = build_network_info()
    installed = _legacy_get_installed_apps()

    nginx_running = running.get("nginx", False)
    apache_running = running.get("apache2", False)

    webserver_ports: list[str] = []
    ports_result = _legacy_run_command("ss -tuln | grep -E ':80|:443|:8000|:8080|:9090|:10000'")
    if ports_result.get("success"):
        stdout = ports_result.get("stdout") or ""
        webserver_ports = stdout.strip().split("\n") if stdout.strip() else []

    pi_installer_port = detect_frontend_port()
    website_names = _legacy_get_website_names()

    cockpit_running = running.get("cockpit", False) or _legacy_check_installed("cockpit")
    webmin_running = running.get("webmin", False) or _legacy_check_installed("webmin")

    cockpit_port = _legacy_run_command("ss -tuln | grep ':9090'")
    webmin_port = _legacy_run_command("ss -tuln | grep ':10000'")

    return {
        "pi_installer": build_webserver_frontend_section(network=network, port=pi_installer_port),
        "website_names": website_names,
        "nginx": {
            "installed": installed.get("nginx", False),
            "running": nginx_running,
        },
        "apache": {
            "installed": installed.get("apache", False),
            "running": apache_running,
        },
        "mysql": {
            "installed": installed.get("mysql", False),
            "running": running.get("mysql", False),
        },
        "mariadb": {
            "installed": installed.get("mariadb", False),
            "running": running.get("mariadb", False),
        },
        "php": {
            "installed": installed.get("php", False),
        },
        "cockpit": {
            "installed": installed.get("cockpit", False),
            "running": cockpit_running or cockpit_port.get("success", False),
            "port": 9090 if cockpit_port.get("success") else None,
        },
        "webmin": {
            "installed": installed.get("webmin", False),
            "running": webmin_running or webmin_port.get("success", False),
            "port": 10000 if webmin_port.get("success") else None,
        },
        "network": network,
        "webserver_ports": webserver_ports,
        "websites": installed.get("websites", []),
        "installed_cms": {
            "wordpress": {
                "installed": installed.get("wordpress", False),
                "plugins": installed.get("wordpress_plugins", []),
            },
            "nextcloud": installed.get("nextcloud", False),
            "drupal": installed.get("drupal", False),
        },
    }


def build_webserver_status_section() -> dict[str, Any]:
    """Webserver status section with facade vocabulary (read-only)."""
    warnings: list[WebserverStatusFacadeWarning] = []
    errors: list[str] = []

    def _build() -> WebserverStatusSection:
        payload = build_webserver_status()
        nginx_running = bool((payload.get("nginx") or {}).get("running"))
        apache_running = bool((payload.get("apache") or {}).get("running"))
        if nginx_running or apache_running:
            section_status = "ok"
        elif (payload.get("nginx") or {}).get("installed") or (payload.get("apache") or {}).get("installed"):
            section_status = "warning"
        else:
            section_status = "unknown"
        return WebserverStatusSection(
            section_id="webserver",
            status=build_section_status(section_status),
            data={"payload": payload},
            warnings=[],
        )

    section = _safe_section("webserver", _build, facade_warnings=warnings, facade_errors=errors)
    return asdict(section)


def build_webserver_status_diagnostics() -> dict[str, Any]:
    """Lightweight facade diagnostics — no active probes."""
    return {
        "facade_version": WEBSERVER_STATUS_FACADE_VERSION,
        "facade_module": "core.webserver_status_facade",
        "status_vocabulary": sorted(FACADE_STATUS_VALUES),
        "delegates_to": [
            "app.get_running_services",
            "app.get_installed_apps",
            "app.get_website_names",
            "app.run_command",
            "app.check_installed",
            "network_info_facade.build_network_info",
            "network_info_facade.detect_frontend_port",
        ],
        "public_functions": [
            "build_webserver_status",
            "build_webserver_status_section",
            "build_webserver_frontend_section",
            "build_webserver_status_diagnostics",
        ],
        "routes_migrated_to_facade": [
            "GET /api/webserver/status",
        ],
        "read_only": True,
        "writes_allowed": False,
        "network_via_network_info_facade": True,
    }
