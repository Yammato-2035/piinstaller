"""Privacy redaction for rescue auto-discovery exports (001D7)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"Bearer\s+\S+", re.I),
    re.compile(r"telemetry-lab-token", re.I),
    re.compile(r"BEGIN\s+(RSA|OPENSSH)\s+PRIVATE\s+KEY", re.I),
)
_PII_KEYS = frozenset(
    {
        "hostname",
        "username",
        "mac",
        "mac_address",
        "serial",
        "serial_number",
        "uuid",
        "partuuid",
        "ip",
        "ip_address",
        "ssid",
        "device_path",
        "mountpoint",
    }
)


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def redact_mapping(data: Any) -> Any:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for key, value in data.items():
            lk = str(key).lower()
            if lk in _PII_KEYS and isinstance(value, str) and value:
                out[key] = f"hash:{_hash_value(value)}"
            else:
                out[key] = redact_mapping(value)
        return out
    if isinstance(data, list):
        return [redact_mapping(item) for item in data]
    if isinstance(data, str):
        text = data
        for pattern in _SECRET_PATTERNS:
            if pattern.search(text):
                return "[REDACTED]"
        return text
    return data


def build_privacy_summary(*, payload: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_mapping(payload)
    blob = str(redacted)
    pii_detected = any(k in blob.lower() for k in ("192.168.", "10.", "00:", "uuid"))
    secret_detected = any(p.search(blob) for p in _SECRET_PATTERNS)
    return {
        "schema": "setuphelfer.rescue.privacy-summary.v1",
        "pii_detected": pii_detected,
        "secret_detected": secret_detected,
        "raw_logs_exported": False,
        "redacted_fields_count": len(_PII_KEYS),
        "summary": redacted,
    }
