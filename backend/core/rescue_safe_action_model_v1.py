"""
Rescue safe action model V1 — action classes with hard safety gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SafeActionClass(str, Enum):
  EXPLAIN_ONLY = "explain_only"
  LOCAL_RESCUE_FIX = "local_rescue_fix"
  TARGET_READONLY_ADVICE = "target_readonly_advice"
  OPERATOR_CONFIRMED_LOW_RISK_FIX = "operator_confirmed_low_risk_fix"
  DESTRUCTIVE_BLOCKED = "destructive_blocked"


DESTRUCTIVE_ACTION_IDS = frozenset(
  {
    "efi_repair",
    "bootloader_write",
    "partition_modify",
    "filesystem_repair",
    "target_apt_install",
    "malware_remove",
    "windows_modify",
    "linux_target_write",
    "dd",
    "mkfs",
    "wipefs",
    "parted_write",
    "restore_original_device",
  }
)

LOCAL_SAFE_ACTION_IDS = frozenset(
  {
    "restart_network_manager_live",
    "rfkill_soft_unblock_wifi",
    "wlan_rescan",
    "retry_telemetry_queue",
    "repair_setup_logs_evidence_path",
    "restart_kiosk_service_live",
    "rerun_local_redaction",
  }
)


@dataclass(frozen=True)
class SafeActionDefinition:
  action_id: str
  action_class: SafeActionClass
  title_de: str
  title_en: str
  reversible: bool
  requires_operator_confirmation: bool
  evidence_required: bool
  allowed_on_target_write: bool = False


SAFE_ACTION_CATALOG: dict[str, SafeActionDefinition] = {
  "restart_network_manager_live": SafeActionDefinition(
    action_id="restart_network_manager_live",
    action_class=SafeActionClass.LOCAL_RESCUE_FIX,
    title_de="NetworkManager im Live-System neu starten",
    title_en="Restart NetworkManager on live system",
    reversible=True,
    requires_operator_confirmation=False,
    evidence_required=True,
  ),
  "rfkill_soft_unblock_wifi": SafeActionDefinition(
    action_id="rfkill_soft_unblock_wifi",
    action_class=SafeActionClass.LOCAL_RESCUE_FIX,
    title_de="WLAN rfkill soft-unblock (Live-System)",
    title_en="WLAN rfkill soft-unblock (live system)",
    reversible=True,
    requires_operator_confirmation=False,
    evidence_required=True,
  ),
  "wlan_rescan": SafeActionDefinition(
    action_id="wlan_rescan",
    action_class=SafeActionClass.LOCAL_RESCUE_FIX,
    title_de="WLAN erneut scannen",
    title_en="Rescan WiFi",
    reversible=True,
    requires_operator_confirmation=False,
    evidence_required=False,
  ),
  "retry_telemetry_queue": SafeActionDefinition(
    action_id="retry_telemetry_queue",
    action_class=SafeActionClass.LOCAL_RESCUE_FIX,
    title_de="Telemetrie-Queue erneut senden",
    title_en="Retry telemetry queue upload",
    reversible=True,
    requires_operator_confirmation=False,
    evidence_required=True,
  ),
  "repair_setup_logs_evidence_path": SafeActionDefinition(
    action_id="repair_setup_logs_evidence_path",
    action_class=SafeActionClass.LOCAL_RESCUE_FIX,
    title_de="SETUP_LOGS Evidence-Pfad reparieren (nur SETUP_LOGS)",
    title_en="Repair SETUP_LOGS evidence path (SETUP_LOGS only)",
    reversible=True,
    requires_operator_confirmation=True,
    evidence_required=True,
  ),
  "efi_repair": SafeActionDefinition(
    action_id="efi_repair",
    action_class=SafeActionClass.DESTRUCTIVE_BLOCKED,
    title_de="EFI reparieren — blockiert",
    title_en="EFI repair — blocked",
    reversible=False,
    requires_operator_confirmation=True,
    evidence_required=True,
    allowed_on_target_write=True,
  ),
}


def classify_action(action_id: str) -> SafeActionDefinition | None:
  if action_id in DESTRUCTIVE_ACTION_IDS:
    return SAFE_ACTION_CATALOG.get(
      action_id,
      SafeActionDefinition(
        action_id=action_id,
        action_class=SafeActionClass.DESTRUCTIVE_BLOCKED,
        title_de=f"{action_id} — destruktiv blockiert",
        title_en=f"{action_id} — destructively blocked",
        reversible=False,
        requires_operator_confirmation=True,
        evidence_required=True,
        allowed_on_target_write=True,
      ),
    )
  return SAFE_ACTION_CATALOG.get(action_id)


def action_allowed_without_operator(action_id: str) -> bool:
  defn = classify_action(action_id)
  if defn is None:
    return False
  if defn.action_class == SafeActionClass.DESTRUCTIVE_BLOCKED:
    return False
  return not defn.requires_operator_confirmation


@dataclass
class SafeActionPlanItem:
  action_id: str
  action_class: SafeActionClass
  status: str
  reason_de: str
  reason_en: str
  operator_confirmed: bool = False
  evidence_ref: str | None = None

  def to_dict(self) -> dict[str, Any]:
    return {
      "action_id": self.action_id,
      "action_class": self.action_class.value,
      "status": self.status,
      "reason_de": self.reason_de,
      "reason_en": self.reason_en,
      "operator_confirmed": self.operator_confirmed,
      "evidence_ref": self.evidence_ref,
    }
