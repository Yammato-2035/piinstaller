"""
Beta machine approval flow contract V1.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

APPROVAL_STATUSES = frozenset({"unknown", "pending", "approved", "blocked", "revoked"})


class MachineApprovalStatus(str, Enum):
  UNKNOWN = "unknown"
  PENDING = "pending"
  APPROVED = "approved"
  BLOCKED = "blocked"
  REVOKED = "revoked"


def validate_machine_entry(entry: dict[str, Any]) -> list[str]:
  errors: list[str] = []
  if not entry.get("machine_fingerprint"):
    errors.append("machine_fingerprint_required")
  status = entry.get("approval_status", "unknown")
  if status not in APPROVAL_STATUSES:
    errors.append("invalid_approval_status")
  return errors


def telemetry_mode_for_machine(status: str, *, agreement_valid: bool) -> str:
  if status == MachineApprovalStatus.APPROVED.value and agreement_valid:
    return "beta_server_accepted"
  if status == MachineApprovalStatus.PENDING.value:
    return "restricted_local_only"
  if status in {MachineApprovalStatus.BLOCKED.value, MachineApprovalStatus.REVOKED.value}:
    return "quarantine"
  return "local_diagnostics_only"


def transition_approval(current: str, action: str) -> str | None:
  if action == "approve" and current in {MachineApprovalStatus.PENDING.value, MachineApprovalStatus.UNKNOWN.value}:
    return MachineApprovalStatus.APPROVED.value
  if action == "block":
    return MachineApprovalStatus.BLOCKED.value
  return None
