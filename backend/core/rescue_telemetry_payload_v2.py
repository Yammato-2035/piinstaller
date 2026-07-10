"""
PI-RS-TEL-004 — Rescue stick telemetry preview payload (telemetry.rescue.beta.v2).

No PII, no secrets, no raw logs. Preview-only; production send remains gated.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from core.rescue_telemetry_client_contract_v2 import (
    CONTRACT_SCHEMA_VERSION,
    validate_telemetry_payload_v2,
)
from core.rescue_telemetry_endpoints import DEFAULT_PROFILE, resolve_rescue_telemetry_profile

PREVIEW_SOURCE_KIND = "rescue_stick"
PREVIEW_EVENT_KIND = CONTRACT_SCHEMA_VERSION

FORBIDDEN_PAYLOAD_TOKENS = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|secret|password|private[_-]?key|BEGIN\s+(RSA\s+)?PRIVATE)"
)

PHYSICAL_STICK_PAYLOAD_VERSION_DEFAULT = "1.10.0.12"
PHYSICAL_STICK_PAYLOAD_SHA256_DEFAULT = (
    "1a72046a40a504e62771a8fc8cd4b6360951c3ac0a4e352a8248fc68f14487e6"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_token(value: str, *, salt: str = "rescue-telemetry-preview") -> str:
    digest = hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()
    return digest[:32]


def _unknown_aggregate_block() -> dict[str, str]:
    return {"status": "unknown"}


def build_diagnostics_aggregates() -> dict[str, dict[str, str]]:
    unknown = "unknown"
    return {
        "plesk": {
            "version": unknown,
            "update_status": unknown,
            "extension_mode": "not_applicable",
        },
        "dns": {
            "records_status": unknown,
            "mx_status": unknown,
            "spf_status": unknown,
        },
        "mail": {
            "service_status": unknown,
            "tls_status": unknown,
            "queue_status": unknown,
        },
        "ssl_tls": {
            "certificate_status": unknown,
            "expiry_status": unknown,
            "mode": unknown,
        },
        "backup": {
            "status": unknown,
            "recent_success": unknown,
            "restore_test": unknown,
        },
    }


def build_rescue_telemetry_preview_payload_v2(
    *,
    workspace_version: str,
    stick_payload_version: str = PHYSICAL_STICK_PAYLOAD_VERSION_DEFAULT,
    payload_sha256: str = PHYSICAL_STICK_PAYLOAD_SHA256_DEFAULT,
    telemetry_endpoint_profile: str = DEFAULT_PROFILE,
    boot_id: str | None = None,
    session_seed: str | None = None,
    device_seed: str | None = None,
    reachability: str = "unknown",
    external_calls: bool = False,
) -> dict[str, Any]:
    profile = resolve_rescue_telemetry_profile(telemetry_endpoint_profile)
    boot_token = boot_id or str(uuid.uuid4())
    session_seed_value = session_seed or boot_token
    device_seed_value = device_seed or "rescue-stick-preview"

    system_assessment: dict[str, Any] = {
        "source_kind": PREVIEW_SOURCE_KIND,
        "event_kind": PREVIEW_EVENT_KIND,
        "production_ready": False,
        "preview_only": True,
        "operator_approval_required": True,
        "auto_apply_enabled": False,
        "external_calls": external_calls,
        "cloud_send_requires_operator_consent": True,
        "device": {
            "device_id_hash": _hash_token(device_seed_value, salt="device"),
        },
        "session": {
            "session_id_hash": _hash_token(session_seed_value, salt="session"),
            "boot_id_hash": _hash_token(boot_token, salt="boot"),
        },
        "build": {
            "workspace_version": workspace_version,
            "stick_payload_version": stick_payload_version,
            "payload_sha256": payload_sha256,
        },
        "network": {
            "reachability": reachability,
            "telemetry_endpoint_profile": profile["profile"],
        },
        "diagnostics_aggregates": build_diagnostics_aggregates(),
    }

    payload: dict[str, Any] = {
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "event_kind": PREVIEW_EVENT_KIND,
        "event_id": str(uuid.uuid4()),
        "created_at": _utc_now(),
        "rescue_version": workspace_version,
        "build_id": payload_sha256[:16],
        "boot_session_id": _hash_token(boot_token, salt="boot-session"),
        "source_kind": PREVIEW_SOURCE_KIND,
        "production_ready": False,
        "preview_only": True,
        "operator_approval_required": True,
        "auto_apply_enabled": False,
        "external_calls": external_calls,
        "cloud_send_requires_operator_consent": True,
        "stick": {
            "stick_id": _hash_token(payload_sha256, salt="stick"),
            "stick_type": "mock",
            "device_public_key_id": "preview-not-provisioned",
            "attestation_mode": "mock",
        },
        "beta": {
            "account_status": "unknown",
            "agreement_status": "missing",
            "upload_allowed": False,
        },
        "machine": {
            "machine_fingerprint": _hash_token(device_seed_value, salt="machine"),
            "approval_status": "unknown",
        },
        "system_assessment": system_assessment,
        "privacy": {
            "redaction_version": "assessment.redaction.v2",
            "contains_mac": False,
            "contains_ip": False,
            "contains_email": False,
            "contains_serial_plaintext": False,
            "contains_file_list": False,
            "contains_user_files": False,
            "contains_secrets": False,
        },
    }
    return payload


def _iter_string_values(obj: Any) -> list[str]:
    values: list[str] = []
    if isinstance(obj, dict):
        for value in obj.values():
            values.extend(_iter_string_values(value))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(_iter_string_values(item))
    elif isinstance(obj, str):
        values.append(obj)
    return values


def validate_preview_payload_security(payload: dict[str, Any]) -> list[str]:
    errors = list(validate_telemetry_payload_v2(payload))
    for value in _iter_string_values(payload):
        if FORBIDDEN_PAYLOAD_TOKENS.search(value):
            errors.append("forbidden_secret_like_token")
            break
    for key in ("mac", "mac_address", "ip_address", "hostname", "email", "raw_log", "secret", "token"):
        if key in payload:
            errors.append(f"forbidden_top_level:{key}")
    assessment = payload.get("system_assessment")
    if isinstance(assessment, dict):
        for forbidden in ("raw_log", "dmesg", "journal", "lspci", "lsusb"):
            if forbidden in assessment:
                errors.append(f"forbidden_assessment:{forbidden}")
    return errors
