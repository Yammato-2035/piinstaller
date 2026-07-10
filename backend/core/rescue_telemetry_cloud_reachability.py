"""
PI-RS-TEL-004 — Gated cloud telemetry reachability (external_calls=false by default).
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

from core.rescue_telemetry_endpoints import (
    DEFAULT_PROFILE,
    build_telemetry_health_url,
    resolve_rescue_telemetry_profile,
)

ENV_EXTERNAL_CALLS = "SETUPHELFER_RESCUE_TELEMETRY_EXTERNAL_CALLS"
REACHABILITY_SCHEMA = "telemetry-cloud-reachability.v1"

HttpProbe = Callable[[str, float], tuple[int | None, str]]


def external_calls_enabled(environ: dict[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return (env.get(ENV_EXTERNAL_CALLS) or "").strip().lower() in {"1", "true", "yes"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_http_probe(url: str, timeout: float) -> tuple[int | None, str]:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Setuphelfer-Rescue-Telemetry/1"})
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
        if "certificate" in msg or "ssl" in msg or "tls" in msg:
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


def probe_cloud_telemetry_health(
    *,
    profile: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 8.0,
    http_probe: HttpProbe | None = None,
    external_calls: bool | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    enabled = external_calls if external_calls is not None else external_calls_enabled(environ)
    prof = resolve_rescue_telemetry_profile(profile or DEFAULT_PROFILE)
    health_url = build_telemetry_health_url(prof, base_url=base_url)
    result: dict[str, Any] = {
        "schema_version": REACHABILITY_SCHEMA,
        "collected_at": _utc_now(),
        "profile": prof["profile"],
        "health_url_redacted": health_url.split("?")[0],
        "external_calls": enabled,
        "preview_only": True,
        "production_ready": False,
    }
    if not enabled:
        result.update(
            {
                "status": "skipped_external_calls_disabled",
                "reachable": False,
                "classification": "external_calls_disabled",
            }
        )
        return result
    probe = http_probe or _default_http_probe
    status, kind = probe(health_url, timeout_seconds)
    if status in {200, 202, 204}:
        result.update({"status": "reachable", "reachable": True, "classification": "ok", "http_status": status})
        return result
    if kind == "tls_error":
        result.update(
            {
                "status": "tls_error",
                "reachable": False,
                "classification": "tls_error",
                "tls_error_documented": True,
            }
        )
        return result
    if kind == "dns_error":
        result.update({"status": "dns_error", "reachable": False, "classification": "dns_error"})
        return result
    if kind == "timeout":
        result.update({"status": "timeout", "reachable": False, "classification": "timeout"})
        return result
    if kind == "http_error":
        result.update(
            {
                "status": "http_error",
                "reachable": False,
                "classification": "http_error",
                "http_status": status,
            }
        )
        return result
    result.update({"status": "unreachable", "reachable": False, "classification": kind})
    return result


def build_cloud_reachability_summary(
    *,
    profile: str | None = None,
    external_calls: bool | None = None,
    http_probe: HttpProbe | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    probe = probe_cloud_telemetry_health(
        profile=profile,
        external_calls=external_calls,
        http_probe=http_probe,
        environ=environ,
    )
    return {
        "schema_version": REACHABILITY_SCHEMA,
        "preview_only": True,
        "production_ready": False,
        "operator_approval_required": True,
        "probe": probe,
        "issue_codes": _issue_codes_from_probe(probe),
    }


def _issue_codes_from_probe(probe: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    classification = probe.get("classification")
    if classification == "ok":
        codes.append("TELEMETRY_CLOUD_HEALTH_OK")
    elif classification == "tls_error":
        codes.append("TELEMETRY_CLOUD_TLS_ERROR")
    elif classification == "dns_error":
        codes.append("TELEMETRY_CLOUD_DNS_ERROR")
    elif classification == "external_calls_disabled":
        codes.append("TELEMETRY_CLOUD_PROBE_SKIPPED")
    elif classification == "http_error":
        codes.append("TELEMETRY_CLOUD_HTTP_ERROR")
    elif not probe.get("reachable"):
        codes.append("TELEMETRY_CLOUD_UNREACHABLE")
    return sorted(set(codes))
