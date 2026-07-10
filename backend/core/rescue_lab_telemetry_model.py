"""
PI-RS-TEL-001 — synthetic Rescue Stick lab telemetry payload model (no PII, no production).
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

RESCUE_LAB_CLIENT_ID_DEFAULT = "fake-rescue-stick-lab-client"
RESCUE_LAB_PRODUCT = "setuphelfer-rescue-stick"
RESCUE_LAB_SOURCE = "rescue_stick_lab_preview"
RESCUE_LAB_ENVIRONMENT = "lab"
RESCUE_LAB_PAYLOAD_KIND = "rescue_preview"
RESCUE_LAB_CREATED_FOR = "PI-RS-TEL-001"

# TEL-012 server wire format uses this payload_kind value at ingest.
TEL012_WIRE_PAYLOAD_KIND = "rescue_stick_lab_preview"

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "mac",
        "mac_address",
        "ip",
        "ip_address",
        "serial",
        "serial_number",
        "hostname",
        "username",
        "email",
        "token",
        "secret",
        "raw_log",
        "ssid",
        "bssid",
        "real_device_id",
    }
)

_MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", re.IGNORECASE)
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class RescueLabTelemetryConfig:
    lab_base_url: str | None
    client_id: str
    secret: str | None
    timeout_seconds: float = 15.0


@dataclass
class RescueLabTelemetryPayload:
    product: str
    source: str
    environment: str
    payload_kind: str
    created_for: str
    rescue_preview: dict[str, Any]
    safety: dict[str, bool]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RescueLabTelemetryEnvelope:
    client_id: str
    payload: dict[str, Any]
    body_bytes: bytes
    headers: dict[str, str]
    ingest_url: str


@dataclass
class RescueLabTelemetryResult:
    status: str
    client_id: str
    product: str
    source: str
    environment: str
    payload_kind: str
    http_status: int | None
    server_status: str | None
    nonce_status: str
    sent_at: str
    production_ready: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_synthetic_rescue_lab_payload(
    *,
    stick_version: str = "lab-preview-1.0",
    gui_available: bool | None = True,
    network_state: str = "unknown",
) -> RescueLabTelemetryPayload:
    if network_state not in {"unknown", "offline", "online", "telemetry_reachable"}:
        network_state = "unknown"
    return RescueLabTelemetryPayload(
        product=RESCUE_LAB_PRODUCT,
        source=RESCUE_LAB_SOURCE,
        environment=RESCUE_LAB_ENVIRONMENT,
        payload_kind=RESCUE_LAB_PAYLOAD_KIND,
        created_for=RESCUE_LAB_CREATED_FOR,
        rescue_preview={
            "stick_version": stick_version,
            "runtime_mode": "rescue_lab_preview",
            "gui_available": gui_available,
            "network_state": network_state,
            "send_flow": "synthetic_lab_only",
        },
        safety={
            "contains_real_host_data": False,
            "contains_raw_logs": False,
            "contains_secrets": False,
            "contains_mac_addresses": False,
            "contains_ip_addresses": False,
            "production_ready": False,
        },
    )


def _walk_values(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_lower = str(key).lower()
            current = f"{path}.{key}" if path else str(key)
            if key_lower in FORBIDDEN_FIELD_NAMES:
                found.append((current, value))
            found.extend(_walk_values(value, current))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_walk_values(item, f"{path}[{idx}]"))
    return found


def _looks_like_forbidden_value(path: str, value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    path_lower = path.lower()
    if "mac" in path_lower and _MAC_RE.match(text):
        return "mac_address"
    if ("ip" in path_lower or "address" in path_lower) and _IPV4_RE.match(text):
        return "ip_address"
    if "hostname" in path_lower and "." in text and "@" not in text:
        return "hostname"
    if "email" in path_lower or _EMAIL_RE.match(text):
        return "email"
    if "raw_log" in path_lower or "log" in path_lower and len(text) > 200:
        return "raw_log"
    return None


def validate_rescue_lab_payload_no_pii(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    violations: list[str] = []
    for path, value in _walk_values(payload):
        key = path.rsplit(".", 1)[-1].lower()
        if key in FORBIDDEN_FIELD_NAMES:
            violations.append(f"forbidden_field:{path}")
        kind = _looks_like_forbidden_value(path, value)
        if kind:
            violations.append(f"forbidden_value:{path}:{kind}")
    safety = payload.get("safety") or {}
    if safety.get("production_ready") is True:
        violations.append("safety.production_ready_must_be_false")
    if payload.get("product") == "setuphelfer-cloudserver-edition":
        violations.append("cross_payload:cloudserver_product_forbidden")
    if payload.get("source") == "cloudserver_lab_preview":
        violations.append("cross_payload:cloudserver_source_forbidden")
    return (len(violations) == 0, violations)


def adapt_payload_for_tel012_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    """Map PI-RS-TEL-001 model fields to TEL-012 server wire contract (no PII added)."""
    wire = dict(payload)
    wire["payload_kind"] = TEL012_WIRE_PAYLOAD_KIND
    wire.setdefault("schema_version", "preview")
    wire.setdefault("source_product", RESCUE_LAB_PRODUCT)
    wire.setdefault("source_version", wire.get("rescue_preview", {}).get("stick_version", "lab-preview"))
    wire.setdefault("collector_version", "rescue-stick-lab-1.0")
    wire.setdefault("collector_mode", "lab_preview")
    wire.setdefault("contains_real_customer_data", False)
    wire.setdefault("contains_secrets", False)
    wire.setdefault("redaction_applied", True)
    wire.setdefault(
        "consent",
        {
            "operator_confirmed": True,
            "scope": "telemetry_preview",
            "raw_logs_included": False,
            "autofix_allowed": False,
        },
    )
    wire.setdefault("audit", {"lab_preview": True, "pi_rs_tel_001": True})
    return wire


def build_rescue_lab_envelope(
    *,
    config: RescueLabTelemetryConfig,
    payload: dict[str, Any],
    secret: str,
) -> RescueLabTelemetryEnvelope:
    from core.rescue_lab_telemetry_signing import build_hmac_headers, wire_json_bytes

    ok, violations = validate_rescue_lab_payload_no_pii(payload)
    if not ok:
        raise ValueError(f"payload_pii_violation:{','.join(violations)}")
    wire_payload = adapt_payload_for_tel012_ingest(payload)
    body_bytes = wire_json_bytes(wire_payload)
    headers = build_hmac_headers(config.client_id, wire_payload, secret)
    from core.rescue_telemetry_endpoints import resolve_telemetry_urls

    base = (config.lab_base_url or "").rstrip("/")
    path_style = os.environ.get("SETUPHELPER_TELEMETRY_LAB_PATH_STYLE", "cloud")
    resolved = resolve_telemetry_urls(base_url=base or None, path_style=path_style)
    ingest_url = resolved["ingest_url"]
    return RescueLabTelemetryEnvelope(
        client_id=config.client_id,
        payload=wire_payload,
        body_bytes=body_bytes,
        headers=headers,
        ingest_url=ingest_url,
    )
