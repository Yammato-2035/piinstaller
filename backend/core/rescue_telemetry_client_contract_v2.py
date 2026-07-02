"""
Rescue telemetry client contract V2 — schema validation and upload mode gating.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

CONTRACT_SCHEMA_VERSION = "telemetry.rescue.beta.v2"

REQUIRED_TOP_LEVEL_KEYS = frozenset(
  {
    "schema_version",
    "event_id",
    "created_at",
    "rescue_version",
    "build_id",
    "boot_session_id",
    "stick",
    "beta",
    "machine",
    "system_assessment",
    "privacy",
  }
)

FORBIDDEN_PRIVACY_TRUE_KEYS = frozenset(
  {
    "contains_mac",
    "contains_ip",
    "contains_email",
    "contains_serial_plaintext",
    "contains_file_list",
    "contains_user_files",
    "contains_secrets",
  }
)


class TelemetryUploadMode(str, Enum):
  DISABLED = "disabled"
  DRY_RUN_LOCAL = "dry_run_local"
  MOCK_SERVER = "mock_server"
  DEV_LAPTOP_LAB = "dev_laptop_lab"
  BETA_SERVER_QUARANTINE = "beta_server_quarantine"
  BETA_SERVER_ACCEPTED = "beta_server_accepted"


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_schema() -> dict[str, Any]:
  path = Path(__file__).resolve().parents[2] / "docs/architecture/telemetry_rescue_beta_v2.schema.json"
  if path.is_file():
    return json.loads(path.read_text(encoding="utf-8"))
  return {"type": "object", "required": list(REQUIRED_TOP_LEVEL_KEYS)}


def build_telemetry_payload_v2(
  *,
  rescue_version: str,
  build_id: str,
  boot_session_id: str,
  stick_id: str,
  stick_type: str,
  device_public_key_id: str,
  attestation_mode: str,
  system_assessment: dict[str, Any],
  account_status: str = "unknown",
  agreement_status: str = "unknown",
  upload_allowed: bool = False,
  machine_fingerprint: str = "unknown",
  approval_status: str = "unknown",
  redaction_version: str = "assessment.redaction.v2",
) -> dict[str, Any]:
  return {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "event_id": str(uuid.uuid4()),
    "created_at": _utc_now(),
    "rescue_version": rescue_version,
    "build_id": build_id,
    "boot_session_id": boot_session_id,
    "stick": {
      "stick_id": stick_id,
      "stick_type": stick_type,
      "device_public_key_id": device_public_key_id,
      "attestation_mode": attestation_mode,
    },
    "beta": {
      "account_status": account_status,
      "agreement_status": agreement_status,
      "upload_allowed": upload_allowed,
    },
    "machine": {
      "machine_fingerprint": machine_fingerprint,
      "approval_status": approval_status,
    },
    "system_assessment": system_assessment,
    "privacy": {
      "redaction_version": redaction_version,
      "contains_mac": False,
      "contains_ip": False,
      "contains_email": False,
      "contains_serial_plaintext": False,
      "contains_file_list": False,
      "contains_user_files": False,
      "contains_secrets": False,
    },
  }


def validate_telemetry_payload_v2(payload: dict[str, Any]) -> list[str]:
  errors: list[str] = []
  if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
    errors.append("schema_version_mismatch")
  missing = REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())
  if missing:
    errors.extend(f"missing:{k}" for k in sorted(missing))
  privacy = payload.get("privacy")
  if not isinstance(privacy, dict):
    errors.append("privacy_missing")
  else:
    for key in FORBIDDEN_PRIVACY_TRUE_KEYS:
      if privacy.get(key) is True:
        errors.append(f"forbidden_privacy:{key}")
  stick = payload.get("stick")
  if isinstance(stick, dict):
    if not stick.get("stick_id"):
      errors.append("stick_id_required")
    if stick.get("stick_type") not in {"team_provisioned", "registered_iso", "mock"}:
      errors.append("stick_type_invalid")
  return errors


def upload_allowed_for_mode(
  mode: TelemetryUploadMode,
  *,
  stick_verified: bool,
  agreement_valid: bool,
) -> tuple[bool, str]:
  if mode == TelemetryUploadMode.DISABLED:
    return False, "disabled"
  if mode in {TelemetryUploadMode.DRY_RUN_LOCAL, TelemetryUploadMode.MOCK_SERVER}:
    return True, "local_or_mock"
  if not stick_verified:
    return False, "stick_not_verified"
  if mode == TelemetryUploadMode.BETA_SERVER_ACCEPTED and not agreement_valid:
    return False, "agreement_missing"
  if mode in {
    TelemetryUploadMode.DEV_LAPTOP_LAB,
    TelemetryUploadMode.BETA_SERVER_QUARANTINE,
    TelemetryUploadMode.BETA_SERVER_ACCEPTED,
  }:
    return True, "ok"
  return False, "unknown_mode"
