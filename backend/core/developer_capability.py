"""Developer DCC capability token gate (separate from rescue telemetry ingest)."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any, Mapping

DCC_TOKEN_ENV = "DCC_DEVELOPER_TOKEN"
DCC_TOKEN_FILE = Path("/etc/setuphelfer/developer.dcc.token")
DCC_HEADER = "x-setuphelfer-developer-token"

RELEASE_LIKE_PROFILES = frozenset({"release", "production"})


def _normalize_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(k).lower(): str(v) for k, v in headers.items()}


def load_configured_dcc_token() -> tuple[str | None, str | None]:
    """Return (token, source) without logging the secret."""
    env_token = (os.environ.get(DCC_TOKEN_ENV) or "").strip()
    if env_token:
        return env_token, "environment"
    if DCC_TOKEN_FILE.is_file():
        try:
            file_token = DCC_TOKEN_FILE.read_text(encoding="utf-8").strip()
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


def _constant_time_equal(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


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

    capability_available = bool(configured)
    capability_valid = bool(
        configured
        and supplied
        and _constant_time_equal(supplied, configured)
    )

    profile_allows_dcc = dev_control_enabled and profile not in RELEASE_LIKE_PROFILES
    dcc_allowed = bool(profile_allows_dcc and capability_valid)

    return {
        "developer_capability_available": capability_available,
        "developer_capability_valid": capability_valid,
        "developer_capability_source": configured_source,
        "developer_capability_configured": capability_available,
        "developer_capability_supplied": bool(supplied),
        "dcc_profile_allowed": profile_allows_dcc,
        "dcc_allowed": dcc_allowed,
        "install_profile": profile,
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
    assessment = assess_developer_capability(
        install_profile=install_profile,
        dev_control_enabled=dev_control_enabled,
        request_headers=request_headers,
    )
    if assessment["dcc_allowed"]:
        return True, None
    if not dev_control_enabled or (install_profile or "").strip().lower() in RELEASE_LIKE_PROFILES:
        return False, "PROFILE_ROUTE_BLOCKED"
    if not assessment["developer_capability_available"]:
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


def developer_capability_block_payload(path: str, block_code: str) -> dict[str, Any]:
    return {
        "status": "error",
        "code": block_code,
        "path": path,
        "dcc_allowed": False,
        "rescue_telemetry_separate_from_dcc": True,
    }
