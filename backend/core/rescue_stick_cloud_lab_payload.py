"""PI-RS-TEL-SEND-001 — redacted Rescue Stick lab telemetry payload builder."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from core.rescue_stick_cloud_lab_models import (
    LAB_EVENT_TYPE,
    LAB_PAYLOAD_SCHEMA_VERSION,
    LAB_SOURCE,
)

_FORBIDDEN_PII_KEYS = frozenset(
    {
        "hostname",
        "host_name",
        "email",
        "mail",
        "username",
        "user_name",
        "customer",
        "domain",
        "fqdn",
        "ipv4",
        "ip_address",
        "mac_address",
        "serial_number",
        "private_key",
        "authorization",
        "token",
        "api_key",
        "secret",
        "hmac",
    }
)

_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_MAC_RE = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")
_HOME_PATH_RE = re.compile(r"/home/[^/\s]+")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def calculate_payload_hash(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def derive_host_id_hash(seed: str = "rescue_stick_lab") -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:32]}"


def build_rescue_stick_lab_payload(
    *,
    stick_version: str,
    boot_mode: str = "lab",
    host_id_hash: str | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body_without_hash = {
        "schema_version": LAB_PAYLOAD_SCHEMA_VERSION,
        "source": LAB_SOURCE,
        "event_type": LAB_EVENT_TYPE,
        "environment": "lab",
        "production_ready": False,
        "contains_pii": False,
        "raw_logs_visible": False,
        "stick_version": stick_version,
        "boot_mode": boot_mode,
        "telemetry_path": "cloud_ingest_verified",
        "host_id_hash": host_id_hash or derive_host_id_hash(),
        "health_status": "health_ok",
        "timestamp": timestamp,
    }
    payload_hash = calculate_payload_hash(body_without_hash)
    return {**body_without_hash, "payload_hash": payload_hash}


_SAFE_VALUE_KEYS = frozenset({"stick_version", "schema_version", "payload_hash", "host_id_hash", "timestamp"})


def assert_no_pii_in_payload(payload: Mapping[str, Any]) -> None:
    lowered_keys = {str(key).lower() for key in payload.keys()}
    forbidden = lowered_keys & _FORBIDDEN_PII_KEYS
    if forbidden:
        raise ValueError(f"forbidden_pii_keys:{sorted(forbidden)}")

    for key, value in payload.items():
        if str(key) in _SAFE_VALUE_KEYS:
            continue
        serialized = canonical_json(value) if isinstance(value, (dict, list)) else str(value)
        if _IPV4_RE.search(serialized):
            raise ValueError("forbidden_plaintext_ipv4")
        if _MAC_RE.search(serialized):
            raise ValueError("forbidden_plaintext_mac")
        if _HOME_PATH_RE.search(serialized):
            raise ValueError("forbidden_home_path")


def redact_payload_for_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    return dict(payload)
