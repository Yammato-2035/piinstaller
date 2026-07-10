"""
PI-RS-TEL-002 — network / telemetry reachability checks (no PII, no host data).
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlparse

from core.rescue_lab_telemetry_config import load_rescue_lab_telemetry_config
from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_CLIENT_ID_DEFAULT,
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
)
from core.rescue_telemetry_endpoints import resolve_telemetry_urls

HttpProbe = Callable[[str, float], tuple[int | None, str]]

_LAST_REACHABILITY: dict[str, Any] | None = None


def redact_lab_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return "[redacted]"
    return f"{parsed.scheme}://{parsed.netloc}/[redacted]"


def check_lab_base_url_configured(lab_base_url: str | None) -> bool:
    return bool((lab_base_url or "").strip())


def check_secret_configured(secret: str | None) -> bool:
    return bool((secret or "").strip())


def build_reachability_config_status(
    *,
    lab_base_url: str | None = None,
    secret: str | None = None,
    client_id: str | None = None,
) -> dict[str, Any]:
    cfg = load_rescue_lab_telemetry_config()
    base = lab_base_url if lab_base_url is not None else cfg.lab_base_url
    sec = secret if secret is not None else cfg.secret
    return {
        "lab_base_url_configured": check_lab_base_url_configured(base),
        "secret_configured": check_secret_configured(sec),
        "client_id": client_id or cfg.client_id or RESCUE_LAB_CLIENT_ID_DEFAULT,
        "lab_base_url_redacted": redact_lab_url(base),
    }


def _default_http_probe(url: str, timeout: float) -> tuple[int | None, str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), "ok"
    except urllib.error.HTTPError as exc:
        return int(exc.code), "http_error"
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            return None, "timeout"
        if isinstance(reason, ssl.SSLError):
            return None, "tls_error"
        if isinstance(reason, socket.gaierror):
            return None, "dns_error"
        msg = str(reason).lower()
        if "timed out" in msg:
            return None, "timeout"
        if "certificate" in msg or "ssl" in msg:
            return None, "tls_error"
        if "name or service not known" in msg or "getaddrinfo" in msg:
            return None, "dns_error"
        return None, "unreachable"
    except TimeoutError:
        return None, "timeout"
    except ssl.SSLError:
        return None, "tls_error"
    except socket.gaierror:
        return None, "dns_error"
    except Exception:
        return None, "unreachable"


def check_network_gate(*, profile_allowed: bool) -> str:
    if not profile_allowed:
        return "blocked_profile_disabled"
    return "unknown"


def check_telemetry_endpoint_reachability(
    lab_base_url: str,
    *,
    timeout_seconds: float = 8.0,
    http_probe: HttpProbe | None = None,
) -> str:
    probe = http_probe or _default_http_probe
    base = lab_base_url.rstrip("/")
    path_style = os.environ.get("SETUPHELPER_TELEMETRY_LAB_PATH_STYLE", "cloud")
    resolved = resolve_telemetry_urls(base_url=base, path_style=path_style)
    health_candidates = [
        resolved["health_url"].removeprefix(base),
        "/v1/telemetry/health",
        "/health",
        "/api/telemetry/health",
        "/",
    ]
    seen: set[str] = set()
    for path in health_candidates:
        if path in seen:
            continue
        seen.add(path)
        url = f"{base}{path}"
        status, kind = probe(url, timeout_seconds)
        if status in {200, 202, 204}:
            return "reachable"
        if kind == "timeout":
            return "timeout"
        if kind == "tls_error":
            return "tls_error"
        if kind == "dns_error":
            return "dns_error"
        if kind == "http_error" and status is not None:
            continue
    return "unreachable"


def build_reachability_summary(
    *,
    profile_allowed: bool,
    lab_base_url: str | None = None,
    secret: str | None = None,
    http_probe: HttpProbe | None = None,
) -> dict[str, Any]:
    global _LAST_REACHABILITY
    cfg = load_rescue_lab_telemetry_config()
    base = lab_base_url if lab_base_url is not None else cfg.lab_base_url
    sec = secret if secret is not None else cfg.secret
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    warnings: list[str] = []
    errors: list[str] = []

    config_status = build_reachability_config_status(lab_base_url=base, secret=sec)
    network_state = check_network_gate(profile_allowed=profile_allowed)
    telemetry_reachability = "not_checked"

    if not profile_allowed:
        network_state = "blocked_profile_disabled"
        telemetry_reachability = "skipped_profile_disabled"
    elif not check_lab_base_url_configured(base):
        network_state = "blocked_missing_config"
        telemetry_reachability = "skipped_missing_config"
        errors.append("lab_base_url_not_configured")
    elif not check_secret_configured(sec):
        network_state = "blocked_missing_secret"
        telemetry_reachability = "skipped_missing_secret"
        errors.append("lab_secret_not_configured")
    else:
        telemetry_reachability = check_telemetry_endpoint_reachability(
            str(base),
            http_probe=http_probe,
        )
        if telemetry_reachability == "reachable":
            network_state = "telemetry_reachable"
        elif telemetry_reachability in {"timeout", "tls_error", "dns_error", "unreachable", "http_error"}:
            network_state = "telemetry_unreachable"
            warnings.append(f"telemetry_reachability:{telemetry_reachability}")
        else:
            network_state = "online_unverified"

    summary = {
        "network_state": network_state,
        "telemetry_reachability": telemetry_reachability,
        "lab_base_url_configured": config_status["lab_base_url_configured"],
        "secret_configured": config_status["secret_configured"],
        "lab_base_url_redacted": config_status["lab_base_url_redacted"],
        "client_id": config_status["client_id"],
        "product": RESCUE_LAB_PRODUCT,
        "source": RESCUE_LAB_SOURCE,
        "environment": RESCUE_LAB_ENVIRONMENT,
        "production_ready": False,
        "checked_at": checked_at,
        "warnings": warnings,
        "errors": errors,
    }
    _LAST_REACHABILITY = summary
    return summary


def get_last_reachability_summary() -> dict[str, Any] | None:
    return _LAST_REACHABILITY


def reset_reachability_for_tests() -> None:
    global _LAST_REACHABILITY
    _LAST_REACHABILITY = None


def reachability_gate_code(summary: dict[str, Any]) -> str:
    if summary.get("errors"):
        return "RESCUE_LAB_TELEMETRY_REACHABILITY_BLOCKED"
    if summary.get("warnings"):
        return "RESCUE_LAB_TELEMETRY_REACHABILITY_REVIEW_REQUIRED"
    if summary.get("telemetry_reachability") == "reachable":
        return "RESCUE_LAB_TELEMETRY_REACHABILITY_OK"
    if summary.get("network_state", "").startswith("blocked"):
        return "RESCUE_LAB_TELEMETRY_REACHABILITY_BLOCKED"
    return "RESCUE_LAB_TELEMETRY_REACHABILITY_REVIEW_REQUIRED"
