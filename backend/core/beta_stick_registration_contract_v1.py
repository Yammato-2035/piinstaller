"""
Beta stick registration and attestation contract V1 (public-safe).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

STICK_TYPES = frozenset({"team_provisioned", "registered_iso"})
STICK_STATUSES = frozenset({"pending", "active", "restricted", "revoked", "suspected_clone"})


class StickType(str, Enum):
  TEAM_PROVISIONED = "team_provisioned"
  REGISTERED_ISO = "registered_iso"


class StickStatus(str, Enum):
  PENDING = "pending"
  ACTIVE = "active"
  RESTRICTED = "restricted"
  REVOKED = "revoked"
  SUSPECTED_CLONE = "suspected_clone"


def validate_stick_registry_entry(entry: dict[str, Any]) -> list[str]:
  errors: list[str] = []
  if entry.get("stick_type") not in STICK_TYPES:
    errors.append("invalid_stick_type")
  if not entry.get("stick_id"):
    errors.append("stick_id_required")
  if not entry.get("device_public_key_id"):
    errors.append("device_public_key_id_required")
  status = entry.get("status")
  if status and status not in STICK_STATUSES:
    errors.append("invalid_status")
  return errors


def detect_suspected_clone(
  *,
  registered_device_key_id: str,
  presented_device_key_id: str,
  stick_id_match: bool,
) -> bool:
  return stick_id_match and registered_device_key_id != presented_device_key_id


def upload_blocked_for_stick(status: str) -> tuple[bool, str]:
  if status == StickStatus.SUSPECTED_CLONE.value:
    return True, "suspected_clone"
  if status == StickStatus.REVOKED.value:
    return True, "revoked"
  if status == StickStatus.RESTRICTED.value:
    return True, "restricted"
  if status == StickStatus.PENDING.value:
    return True, "pending_activation"
  return False, "ok"
