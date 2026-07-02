"""
Beta agreement and consent gate V1.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

AGREEMENT_STATUSES = frozenset({"missing", "pending", "valid", "expired", "revoked"})
QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT = 14

# Explicit policy: no identity document fields
FORBIDDEN_ID_DOCUMENT_FIELDS = frozenset(
  {
    "id_card_number",
    "passport_number",
    "national_id",
    "identity_document_scan",
    "ausweisnummer",
    "personalausweis",
  }
)


class AgreementStatus(str, Enum):
  MISSING = "missing"
  PENDING = "pending"
  VALID = "valid"
  EXPIRED = "expired"
  REVOKED = "revoked"


def validate_no_id_documents(payload: dict[str, Any]) -> list[str]:
  violations: list[str] = []

  def walk(obj: Any, key: str = "") -> None:
    if key.lower() in FORBIDDEN_ID_DOCUMENT_FIELDS:
      violations.append(f"forbidden_field:{key}")
    if isinstance(obj, dict):
      for k, v in obj.items():
        walk(v, str(k))
    elif isinstance(obj, list):
      for item in obj:
        walk(item, key)

  walk(payload)
  return violations


def gate_upload(
  *,
  agreement_status: str,
  telemetry_consent: bool,
  mfa_enabled: bool,
  email_verified: bool,
) -> dict[str, Any]:
  if not email_verified:
    return {"allowed": False, "mode": "quarantine", "reason": "email_not_verified"}
  if not mfa_enabled:
    return {"allowed": False, "mode": "restricted_local_only", "reason": "mfa_required"}
  if agreement_status == AgreementStatus.MISSING.value:
    return {
      "allowed": False,
      "mode": "quarantine",
      "reason": "agreement_missing",
      "retention_days": QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT,
    }
  if agreement_status == AgreementStatus.EXPIRED.value:
    return {"allowed": False, "mode": "quarantine", "reason": "agreement_expired"}
  if not telemetry_consent:
    return {"allowed": False, "mode": "restricted_local_only", "reason": "telemetry_consent_missing"}
  if agreement_status == AgreementStatus.VALID.value:
    return {"allowed": True, "mode": "beta_server_accepted", "reason": "ok"}
  return {"allowed": False, "mode": "quarantine", "reason": "agreement_pending"}
