"""
Rescue repair advice engine V1 — maps issue codes to safe action plans.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.rescue_issue_codes_v2 import RescueIssueCodeV2
from core.rescue_recommendation_codes_v2 import RescueRecommendationCodeV2
from core.rescue_safe_action_model_v1 import (
  SafeActionClass,
  SafeActionPlanItem,
  classify_action,
)

PLAN_SCHEMA_VERSION = "safe-action-plan.v1"

_ISSUE_TO_ACTIONS: dict[str, list[str]] = {
  RescueIssueCodeV2.NETWORK_WIFI_UNCONNECTED.value: ["wlan_rescan", "restart_network_manager_live"],
  RescueIssueCodeV2.NETWORK_WIFI_BLOCKED_BY_LAN_REGRESSION.value: ["wlan_rescan", "restart_network_manager_live"],
  RescueIssueCodeV2.RFKILL_BLOCKED.value: ["rfkill_soft_unblock_wifi"],
  RescueIssueCodeV2.TELEMETRY_ENDPOINT_UNREACHABLE.value: ["retry_telemetry_queue"],
  RescueIssueCodeV2.DNS_FAILED.value: ["restart_network_manager_live"],
  RescueIssueCodeV2.PCIE_AER_FATAL.value: ["efi_repair"],
  RescueIssueCodeV2.STORAGE_SMART_WARNING.value: ["efi_repair"],
}


def _utc_now() -> str:
  return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_safe_action_plan(
  issue_codes: list[str],
  recommendation_codes: list[str] | None = None,
  *,
  operator_confirmed_actions: set[str] | None = None,
) -> dict[str, Any]:
  confirmed = operator_confirmed_actions or set()
  seen: set[str] = set()
  items: list[SafeActionPlanItem] = []

  for code in issue_codes:
    for action_id in _ISSUE_TO_ACTIONS.get(code, []):
      if action_id in seen:
        continue
      seen.add(action_id)
      defn = classify_action(action_id)
      if defn is None:
        continue
      if defn.action_class == SafeActionClass.DESTRUCTIVE_BLOCKED:
        items.append(
          SafeActionPlanItem(
            action_id=action_id,
            action_class=SafeActionClass.DESTRUCTIVE_BLOCKED,
            status="blocked",
            reason_de="Destruktive Aktion — nur manuelle Anleitung",
            reason_en="Destructive action — manual guide only",
          )
        )
      elif defn.requires_operator_confirmation and action_id not in confirmed:
        items.append(
          SafeActionPlanItem(
            action_id=action_id,
            action_class=defn.action_class,
            status="pending_operator",
            reason_de="Operator-Freigabe erforderlich",
            reason_en="Operator confirmation required",
          )
        )
      else:
        items.append(
          SafeActionPlanItem(
            action_id=action_id,
            action_class=defn.action_class,
            status="allowed",
            reason_de="Sichere lokale Aktion erlaubt",
            reason_en="Safe local action allowed",
            operator_confirmed=action_id in confirmed,
          )
        )

  if not items:
    items.append(
      SafeActionPlanItem(
        action_id="explain_only",
        action_class=SafeActionClass.EXPLAIN_ONLY,
        status="allowed",
        reason_de="Nur Erklärung — keine automatische Behebung",
        reason_en="Explain only — no automatic fix",
      )
    )

  return {
    "schema_version": PLAN_SCHEMA_VERSION,
    "created_at": _utc_now(),
    "issue_codes": issue_codes,
    "recommendation_codes": recommendation_codes or [],
    "actions": [i.to_dict() for i in items],
    "destructive_blocked_count": sum(1 for i in items if i.status == "blocked"),
    "operator_pending_count": sum(1 for i in items if i.status == "pending_operator"),
  }
