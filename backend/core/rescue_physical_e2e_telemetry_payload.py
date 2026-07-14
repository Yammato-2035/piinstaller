"""Telemetry payload builder for physical E2E — telemetry.rescue.beta.v2."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from core.rescue_physical_e2e_models import TELEMETRY_SCHEMA
from core.rescue_telemetry_client_contract_v2 import validate_telemetry_payload_v2

_FORBIDDEN_VALUE = re.compile(
    r"(?i)(api[_-]?key|authorization:\s*|bearer\s+\S|password\s*[=:]|private[_-]?key|BEGIN\s+(RSA\s+)?PRIVATE|"
    r"/home/[^/\s]+|(?:\d{1,3}\.){3}\d{1,3}|(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})"
)
_FORBIDDEN_KEYS = frozenset(
    {"hostname", "email", "username", "mac_address", "serial_number", "token", "authorization", "api_key", "secret"}
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_token(value: str, *, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:32]


_SAFE_VALUE_KEYS = frozenset(
    {
        "schema_version",
        "rescue_version",
        "payload_version",
        "build_id",
        "stick_version",
        "redaction_version",
        "signing_version",
        "event_id",
        "e2e_run_id",
        "rescue_session_id",
        "backup_job_id",
        "restore_job_id",
        "boot_session_id",
        "created_at",
        "operation_event",
        "stick_id",
        "stick_type",
        "device_public_key_id",
        "attestation_mode",
        "machine_fingerprint",
        "approval_status",
        "account_status",
        "agreement_status",
        "cpu_class",
        "backup_format",
        "operation_status",
        "session_phase",
        "restore_integrity_status",
        "engine",
        "diagnostics_status",
    }
)


def _scan_value(value: Any, *, parent_key: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ValueError("payload_contains_forbidden_key")
            _scan_value(item, parent_key=str(key))
        return
    if isinstance(value, list):
        for item in value:
            _scan_value(item, parent_key=parent_key)
        return
    if parent_key in _SAFE_VALUE_KEYS:
        return
    if isinstance(value, bool) or value is None:
        return
    text = str(value)
    if _FORBIDDEN_VALUE.search(text):
        raise ValueError("payload_contains_forbidden_content")


def assert_payload_no_pii(payload: dict[str, Any]) -> None:
    _scan_value(payload)


def build_physical_e2e_telemetry_payload(
    *,
    operation_event: str,
    event_id: str,
    e2e_run_id: str,
    rescue_session_id: str,
    device_id_hash: str,
    rescue_version: str,
    payload_sha256: str,
    backup_job_id: str | None = None,
    restore_job_id: str | None = None,
    assessment: dict[str, Any] | None = None,
    stick_id: str = "stick-e2e-live",
    operation_status: str = "completed",
    created_at: str | None = None,
) -> dict[str, Any]:
    base_assessment: dict[str, Any] = {
        "operation_event": operation_event,
        "e2e_run_id": e2e_run_id,
        "rescue_session_id": rescue_session_id,
        "backup_job_id": backup_job_id or "",
        "restore_job_id": restore_job_id or "",
        "payload_version": rescue_version,
        "cpu_class": "generic",
        "operation_status": operation_status,
        "production_ready": False,
    }
    if assessment:
        base_assessment.update(assessment)

    payload: dict[str, Any] = {
        "schema_version": TELEMETRY_SCHEMA,
        "event_id": event_id,
        "created_at": created_at or _utc_now(),
        "rescue_version": rescue_version,
        "build_id": payload_sha256[:16] if payload_sha256 else "unknown",
        "boot_session_id": _hash_token(rescue_session_id, salt="boot-session"),
        "stick": {
            "stick_id": stick_id,
            "stick_type": "registered_iso",
            "device_public_key_id": "key-lab",
            "attestation_mode": "hmac",
        },
        "beta": {"account_status": "verified", "agreement_status": "valid", "upload_allowed": True},
        "machine": {"machine_fingerprint": device_id_hash, "approval_status": "approved"},
        "system_assessment": base_assessment,
        "privacy": {
            "redaction_version": "1",
            "contains_mac": False,
            "contains_ip": False,
            "contains_email": False,
            "contains_serial_plaintext": False,
            "contains_file_list": False,
            "contains_user_files": False,
            "contains_secrets": False,
        },
    }
    assert_payload_no_pii(payload)
    validation_errors = validate_telemetry_payload_v2(payload)
    if validation_errors:
        raise ValueError(f"invalid_telemetry_payload:{','.join(validation_errors)}")
    return payload


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def new_event_id() -> str:
    return str(uuid.uuid4())


def new_e2e_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"e2e-rescue-physical-{stamp}-{uuid.uuid4().hex[:8]}"
