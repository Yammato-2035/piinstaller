from __future__ import annotations

import hashlib
import ipaddress
from urllib.parse import urlparse


def hash_endpoint(endpoint: str) -> str:
    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()


def _is_private_or_local_host(host: str) -> bool:
    host_l = host.lower()
    if host_l in {"localhost", "127.0.0.1"} or host_l.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host_l)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def validate_endpoint(endpoint: str, *, allow_public: bool = False) -> tuple[bool, list[str]]:
    errors: list[str] = []
    parsed = urlparse((endpoint or "").strip())
    if parsed.scheme not in {"http", "https"}:
        errors.append("invalid_scheme")
    if not parsed.hostname:
        errors.append("missing_hostname")
    elif not allow_public and not _is_private_or_local_host(parsed.hostname):
        errors.append("public_endpoint_blocked")
    return (not errors, errors)


def discover_devserver(
    *,
    profile: str,
    rescue_mode_enabled: bool,
    boot_param_endpoint: str | None = None,
    config_endpoint: str | None = None,
    mdns_endpoint: str | None = None,
    udp_endpoint: str | None = None,
    allow_udp_broadcast: bool = False,
    allow_public_endpoint: bool = False,
) -> dict:
    if profile == "release" and not rescue_mode_enabled:
        return {
            "discovery_status": "disabled",
            "method": "none",
            "endpoint": "",
            "endpoint_hash": "",
            "warnings": ["discovery_disabled_in_release"],
            "errors": [],
        }

    candidates = [
        ("boot_param", boot_param_endpoint),
        ("config", config_endpoint),
        ("mdns", mdns_endpoint),
        ("udp_broadcast", udp_endpoint if allow_udp_broadcast else None),
    ]
    for method, endpoint in candidates:
        if not endpoint:
            continue
        ok, errors = validate_endpoint(endpoint, allow_public=allow_public_endpoint)
        if not ok:
            return {
                "discovery_status": "blocked",
                "method": method,
                "endpoint": "",
                "endpoint_hash": "",
                "warnings": [],
                "errors": errors,
            }
        return {
            "discovery_status": "found",
            "method": method,
            "endpoint": endpoint,
            "endpoint_hash": hash_endpoint(endpoint),
            "warnings": [],
            "errors": [],
        }

    return {
        "discovery_status": "not_found",
        "method": "none",
        "endpoint": "",
        "endpoint_hash": "",
        "warnings": ["devserver_not_found"],
        "errors": [],
    }

