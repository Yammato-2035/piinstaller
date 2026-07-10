"""Canonical rescue telemetry endpoint configuration (no secrets, no network I/O)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _REPO_ROOT / "config" / "rescue_telemetry_endpoints.json"

CLOUD_BASE_URL_DEFAULT = "https://telemetrie.setuphelfer.de"
CLOUD_HEALTH_PATH = "/v1/telemetry/health"
CLOUD_INGEST_PATH = "/v1/telemetry/ingest"
CLOUD_SCHEMA = "telemetry.rescue.beta.v2"

LEGACY_LOCAL_BASE_URL = "http://192.168.178.140:8001"
LEGACY_HEALTH_PATH = "/api/rescue/telemetry/health"
LEGACY_INGEST_PATH = "/api/rescue/telemetry/v1/ingest"
LEGACY_SCHEMA = "rescue_boot_network_telemetry"

DEFAULT_PROFILE = "cloud"
LEGACY_PROFILE = "legacy_lan_lab"

_CREDENTIALS_IN_URL = re.compile(r"://[^/@]+:[^/@]+@")


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


@lru_cache(maxsize=1)
def load_rescue_telemetry_endpoint_config() -> dict[str, Any]:
    if not _CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_rescue_telemetry_profile(profile: str | None = None) -> dict[str, Any]:
    cfg = load_rescue_telemetry_endpoint_config()
    name = (profile or cfg.get("default_profile") or DEFAULT_PROFILE).strip()
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}
    raw = profiles.get(name) if isinstance(profiles.get(name), dict) else {}
    if name == LEGACY_PROFILE or name in {"legacy", "local", "local_backend_proxy"}:
        return {
            "profile": LEGACY_PROFILE,
            "base_url": str(raw.get("base_url") or LEGACY_LOCAL_BASE_URL).strip(),
            "path_style": str(raw.get("path_style") or "legacy").strip(),
            "health_path": str(raw.get("health_path") or LEGACY_HEALTH_PATH).strip(),
            "ingest_path": str(raw.get("ingest_path") or LEGACY_INGEST_PATH).strip(),
            "schema": str(raw.get("schema") or LEGACY_SCHEMA).strip(),
            "production_ready": bool(raw.get("production_ready", False)),
            "operator_consent_required": bool(raw.get("operator_consent_required", True)),
            "legacy": True,
        }
    return {
        "profile": DEFAULT_PROFILE,
        "base_url": str(raw.get("base_url") or CLOUD_BASE_URL_DEFAULT).strip(),
        "path_style": str(raw.get("path_style") or "cloud").strip(),
        "health_path": str(raw.get("health_path") or CLOUD_HEALTH_PATH).strip(),
        "ingest_path": str(raw.get("ingest_path") or CLOUD_INGEST_PATH).strip(),
        "schema": str(raw.get("schema") or CLOUD_SCHEMA).strip(),
        "production_ready": bool(raw.get("production_ready", False)),
        "operator_consent_required": bool(raw.get("operator_consent_required", True)),
        "legacy": False,
    }


def build_telemetry_health_url(profile: dict[str, Any] | None = None, *, base_url: str | None = None) -> str:
    prof = profile or resolve_rescue_telemetry_profile()
    base = (base_url or prof["base_url"]).rstrip("/")
    reject_credentials_in_url(base)
    return _join_url(base, str(prof["health_path"]))


def build_telemetry_ingest_url(profile: dict[str, Any] | None = None, *, base_url: str | None = None) -> str:
    prof = profile or resolve_rescue_telemetry_profile()
    base = (base_url or prof["base_url"]).rstrip("/")
    reject_credentials_in_url(base)
    return _join_url(base, str(prof["ingest_path"]))


def reject_credentials_in_url(url: str) -> None:
    if not url or not isinstance(url, str):
        raise ValueError("url_required")
    if _CREDENTIALS_IN_URL.search(url):
        raise ValueError("credentials_in_url_rejected")
    parsed = urlparse(url.strip())
    if parsed.username or parsed.password:
        raise ValueError("credentials_in_url_rejected")


def classify_endpoint_kind(url: str) -> str:
    reject_credentials_in_url(url)
    parsed = urlparse(url.strip())
    path = parsed.path or ""
    if "/v1/telemetry/" in path:
        return "cloud"
    if "/api/rescue/telemetry/" in path:
        return "legacy"
    if parsed.scheme == "https":
        return "cloud"
    if parsed.hostname in {"127.0.0.1", "localhost"}:
        return "dev_local"
    return "unknown"


def resolve_telemetry_urls(
    *,
    base_url: str | None = None,
    path_style: str | None = None,
    profile: str | None = None,
) -> dict[str, str]:
    """Backward-compatible URL resolver used by lab reachability and shell parity."""
    style = (path_style or "cloud").strip().lower()
    prof_name = LEGACY_PROFILE if style in {"legacy", "local", "local_backend_proxy"} else (profile or DEFAULT_PROFILE)
    prof = resolve_rescue_telemetry_profile(prof_name)
    base = (base_url or prof["base_url"]).rstrip("/")
    reject_credentials_in_url(base)
    return {
        "base_url": base,
        "path_style": prof["path_style"],
        "profile": prof["profile"],
        "schema": prof["schema"],
        "health_url": build_telemetry_health_url(prof, base_url=base),
        "ingest_url": build_telemetry_ingest_url(prof, base_url=base),
    }


def production_telemetry_profile() -> dict[str, str]:
    prof = resolve_rescue_telemetry_profile(DEFAULT_PROFILE)
    base = prof["base_url"]
    return {
        "base_url": base,
        "path_style": prof["path_style"],
        "health_url": build_telemetry_health_url(prof),
        "ingest_url": build_telemetry_ingest_url(prof),
    }


def legacy_local_telemetry_profile() -> dict[str, str]:
    prof = resolve_rescue_telemetry_profile(LEGACY_PROFILE)
    base = prof["base_url"]
    return {
        "base_url": base,
        "path_style": prof["path_style"],
        "health_url": build_telemetry_health_url(prof),
        "ingest_url": build_telemetry_ingest_url(prof),
    }


# Backward-compatible alias
load_rescue_telemetry_endpoints_config = load_rescue_telemetry_endpoint_config
