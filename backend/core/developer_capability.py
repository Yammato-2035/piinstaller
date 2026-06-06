"""Developer DCC capability token gate (separate from rescue telemetry ingest)."""

from __future__ import annotations

import os
import secrets
import socket
from pathlib import Path
from typing import Any, Mapping

DCC_TOKEN_ENV = "DCC_DEVELOPER_TOKEN"
DCC_DEVELOPER_ENABLED_ENV = "DCC_DEVELOPER_ENABLED"
DCC_TOKEN_FILE_ENV = "DCC_DEVELOPER_TOKEN_FILE"
DCC_ALLOWED_HOSTNAME_ENV = "DCC_ALLOWED_HOSTNAME"
DCC_DEVELOPER_ENV_FILE = Path("/etc/setuphelfer/developer.env")
DCC_TOKEN_FILE_DEFAULT = Path("/etc/setuphelfer/dcc_developer.token")
DCC_TOKEN_FILE_LEGACY = Path("/etc/setuphelfer/developer.dcc.token")
DCC_HEADER = "x-setuphelfer-developer-token"
CAPABILITY_STATUS_PATH = "/api/dev-dashboard/capability-status"
COMPACT_STATUS_PATH = "/api/dev-dashboard/compact-status"

RELEASE_LIKE_PROFILES = frozenset({"release", "production"})
LAB_PROFILES = frozenset({"developer", "local_lab"})

_ENV_FILE_LOADED = False


def _env_truthy(key: str) -> bool:
    return (os.environ.get(key) or "").strip().lower() in ("1", "true", "yes", "on")


def _load_developer_env_file() -> None:
    """Load /etc/setuphelfer/developer.env into os.environ (unset keys only)."""
    global _ENV_FILE_LOADED
    if _ENV_FILE_LOADED:
        return
    _ENV_FILE_LOADED = True
    if not DCC_DEVELOPER_ENV_FILE.is_file():
        return
    try:
        for line in DCC_DEVELOPER_ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, value = stripped.partition("=")
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip()
    except OSError:
        return


def is_dcc_developer_enabled() -> bool:
    _load_developer_env_file()
    return _env_truthy(DCC_DEVELOPER_ENABLED_ENV)


def _normalize_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(k).lower(): str(v) for k, v in headers.items()}


def _token_file_candidates() -> list[Path]:
    _load_developer_env_file()
    configured = (os.environ.get(DCC_TOKEN_FILE_ENV) or "").strip()
    paths: list[Path] = []
    if configured:
        paths.append(Path(configured))
    paths.append(DCC_TOKEN_FILE_DEFAULT)
    paths.append(DCC_TOKEN_FILE_LEGACY)
    return paths


def load_configured_dcc_token() -> tuple[str | None, str | None]:
    """Return (token, source) without logging the secret."""
    _load_developer_env_file()
    env_token = (os.environ.get(DCC_TOKEN_ENV) or "").strip()
    if env_token:
        return env_token, "environment"
    for path in _token_file_candidates():
        if path.is_file():
            try:
                file_token = path.read_text(encoding="utf-8").strip()
            except OSError:
                file_token = ""
            if file_token:
                return file_token, "file"
    return None, None


def extract_supplied_dcc_token(headers: Mapping[str, str] | None) -> str | None:
    hdrs = _normalize_headers(headers)
    auth = hdrs.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        return token or None
    header_token = hdrs.get(DCC_HEADER) or ""
    return header_token.strip() or None


def check_machine_binding() -> tuple[bool, bool]:
    """Return (hostname_ok, binding_checked)."""
    _load_developer_env_file()
    allowed = (os.environ.get(DCC_ALLOWED_HOSTNAME_ENV) or "").strip()
    if not allowed:
        return True, False
    try:
        hostname = socket.gethostname().strip()
    except OSError:
        hostname = ""
    return hostname == allowed, True


def _constant_time_equal(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _path_base(path: str) -> str:
    return path.split("?")[0].rstrip("/") or "/"


def _dcc_route_open(
    *,
    profile: str,
    dev_control_enabled: bool,
    configured: bool,
    hostname_ok: bool,
) -> bool:
    if not configured or not hostname_ok:
        return False
    if profile in LAB_PROFILES:
        return dev_control_enabled
    if profile in RELEASE_LIKE_PROFILES:
        return is_dcc_developer_enabled()
    return False


def _resolve_capability_reason(
    *,
    profile: str,
    dev_control_enabled: bool,
    dcc_allowed: bool,
    capability_valid: bool,
    configured: bool,
    hostname_ok: bool,
    machine_binding_checked: bool,
    dcc_route_open: bool,
) -> str:
    if dcc_allowed and capability_valid:
        if profile == "local_lab":
            return "LOCAL_LAB_ALLOWED"
        return "DEVELOPER_CAPABILITY_VALID"
    if profile in RELEASE_LIKE_PROFILES and not is_dcc_developer_enabled():
        return "PROFILE_ROUTE_BLOCKED"
    if profile in LAB_PROFILES and not dev_control_enabled:
        return "PROFILE_ROUTE_BLOCKED"
    if machine_binding_checked and not hostname_ok:
        return "DEVELOPER_CAPABILITY_REQUIRED"
    if dcc_route_open or configured:
        return "DEVELOPER_CAPABILITY_REQUIRED"
    return "PROFILE_ROUTE_BLOCKED"


def assess_developer_capability(
    *,
    install_profile: str,
    dev_control_enabled: bool,
    request_headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Evaluate DCC capability without exposing token values."""
    profile = (install_profile or "release").strip().lower()
    configured, configured_source = load_configured_dcc_token()
    supplied = extract_supplied_dcc_token(request_headers)
    hostname_ok, machine_binding_checked = check_machine_binding()

    token_match = bool(
        configured and supplied and _constant_time_equal(supplied, configured)
    )
    capability_valid = bool(token_match and hostname_ok)
    dcc_route_open = _dcc_route_open(
        profile=profile,
        dev_control_enabled=dev_control_enabled,
        configured=bool(configured),
        hostname_ok=hostname_ok,
    )
    dcc_allowed = bool(dcc_route_open and capability_valid)

    return {
        "developer_capability_available": bool(configured),
        "developer_capability_valid": capability_valid,
        "developer_capability_source": configured_source,
        "developer_capability_configured": bool(configured),
        "developer_capability_supplied": bool(supplied),
        "dcc_developer_enabled": is_dcc_developer_enabled(),
        "dcc_route_open": dcc_route_open,
        "dcc_profile_allowed": profile in LAB_PROFILES and dev_control_enabled,
        "dcc_allowed": dcc_allowed,
        "dcc_visible": dcc_allowed,
        "install_profile": profile,
        "machine_binding_checked": machine_binding_checked,
        "machine_binding_ok": hostname_ok,
        "token_source_present": bool(configured),
        "internal_dev_mode": dcc_allowed,
        "rescue_telemetry_separate_from_dcc": True,
    }


def is_dcc_route_allowed(
    *,
    path: str,
    install_profile: str,
    dev_control_enabled: bool,
    request_headers: Mapping[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Return (allowed, block_code)."""
    if not path.startswith("/api/dev-dashboard"):
        return True, None
    if _path_base(path) in (CAPABILITY_STATUS_PATH, COMPACT_STATUS_PATH):
        return True, None

    assessment = assess_developer_capability(
        install_profile=install_profile,
        dev_control_enabled=dev_control_enabled,
        request_headers=request_headers,
    )
    if assessment["dcc_allowed"]:
        return True, None

    profile = (install_profile or "release").strip().lower()
    if profile in RELEASE_LIKE_PROFILES and not is_dcc_developer_enabled():
        return False, "PROFILE_ROUTE_BLOCKED"
    if profile in LAB_PROFILES and not dev_control_enabled:
        return False, "PROFILE_ROUTE_BLOCKED"
    if not assessment["developer_capability_configured"]:
        return False, "DEVELOPER_CAPABILITY_NOT_CONFIGURED"
    return False, "DEVELOPER_CAPABILITY_REQUIRED"


def developer_capability_status_for_api(
    *,
    install_profile: str,
    dev_control_enabled: bool,
) -> dict[str, Any]:
    """Public status fields for /api/version (no request token, no secret)."""
    return assess_developer_capability(
        install_profile=install_profile,
        dev_control_enabled=dev_control_enabled,
        request_headers=None,
    )


def build_capability_status_payload(
    *,
    install_profile: str,
    dev_control_enabled: bool,
    backend_runtime_path: str,
    request_headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Read-only DCC gate diagnosis — no secrets."""
    assessment = assess_developer_capability(
        install_profile=install_profile,
        dev_control_enabled=dev_control_enabled,
        request_headers=request_headers,
    )
    profile = (install_profile or "release").strip().lower()
    reason = _resolve_capability_reason(
        profile=profile,
        dev_control_enabled=dev_control_enabled,
        dcc_allowed=bool(assessment["dcc_allowed"]),
        capability_valid=bool(assessment["developer_capability_valid"]),
        configured=bool(assessment["developer_capability_configured"]),
        hostname_ok=bool(assessment["machine_binding_ok"]),
        machine_binding_checked=bool(assessment["machine_binding_checked"]),
        dcc_route_open=bool(assessment["dcc_route_open"]),
    )
    return {
        "dcc_visible": bool(assessment["dcc_visible"]),
        "reason": reason,
        "install_profile": profile,
        "dev_control_enabled": dev_control_enabled,
        "developer_capability_configured": bool(assessment["developer_capability_configured"]),
        "developer_capability_valid": bool(assessment["developer_capability_valid"]),
        "token_source_present": bool(assessment["token_source_present"]),
        "machine_binding_checked": bool(assessment["machine_binding_checked"]),
        "dcc_developer_enabled": bool(assessment["dcc_developer_enabled"]),
        "backend_runtime_path": backend_runtime_path,
        "rescue_telemetry_separate_from_dcc": True,
        "dev_server_locally_allowed": is_dev_server_host_locally_allowed(
            install_profile=profile,
            dev_control_enabled=dev_control_enabled,
        ),
    }


def is_dev_server_host_locally_allowed(
    *,
    install_profile: str | None = None,
    dev_control_enabled: bool | None = None,
) -> bool:
    """Host-level Dev Server allowance (no request token, no secrets)."""
    if install_profile is None or dev_control_enabled is None:
        from core.install_profile import get_install_profile_state

        state = get_install_profile_state()
        install_profile = state.install_profile
        dev_control_enabled = state.dev_control_enabled
    profile = (install_profile or "release").strip().lower()
    if profile in LAB_PROFILES and dev_control_enabled:
        return True
    assessment = assess_developer_capability(
        install_profile=profile,
        dev_control_enabled=bool(dev_control_enabled),
        request_headers=None,
    )
    return bool(assessment.get("dcc_route_open") and assessment.get("developer_capability_configured"))


def developer_capability_host_exemption_summary() -> dict[str, Any]:
    """Host-level DCC exemption for deploy drift (no request token, no secrets)."""
    from core.install_profile import get_install_profile_state

    state = get_install_profile_state()
    assessment = assess_developer_capability(
        install_profile=state.install_profile,
        dev_control_enabled=state.dev_control_enabled,
        request_headers=None,
    )
    locally_allowed = bool(
        assessment.get("dcc_route_open")
        and assessment.get("developer_capability_configured")
    )
    return {
        "status": "allowed" if locally_allowed else "inactive",
        "locally_allowed_on_host": locally_allowed,
        "dcc_developer_enabled": bool(assessment.get("dcc_developer_enabled")),
        "developer_capability_configured": bool(assessment.get("developer_capability_configured")),
        "machine_binding_checked": bool(assessment.get("machine_binding_checked")),
        "machine_binding_ok": bool(assessment.get("machine_binding_ok")),
        "install_profile": state.install_profile,
    }


def developer_capability_block_payload(path: str, block_code: str) -> dict[str, Any]:
    return {
        "status": "error",
        "code": block_code,
        "path": path,
        "dcc_allowed": False,
        "rescue_telemetry_separate_from_dcc": True,
    }
