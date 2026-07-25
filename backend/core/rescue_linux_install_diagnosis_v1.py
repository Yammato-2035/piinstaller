"""
Linux / dual-NVMe install failure diagnosis — read-only classification.
"""

from __future__ import annotations

from typing import Any

from core.rescue_issue_codes_v2 import RescueIssueCodeV2
from core.rescue_recommendation_codes_v2 import RescueRecommendationCodeV2

DIAGNOSIS_SCHEMA = "linux-install-diagnosis.v1"


def classify_install_diagnosis(
  *,
  bios_compare: dict[str, Any] | None = None,
  assessment_issue_codes: list[str] | None = None,
  secure_boot: str | None = None,
  iso_sha256_ok: bool | None = None,
  disk_roles_bound: bool = False,
  nvme_count: int = 0,
) -> dict[str, Any]:
  codes: list[str] = []
  recommendations: list[str] = []
  issues = set(assessment_issue_codes or [])

  if RescueIssueCodeV2.PCIE_AER_FATAL.value in issues or RescueIssueCodeV2.PCIE_AER_NONFATAL.value in issues:
    codes.append(RescueIssueCodeV2.PCIE_AER_FLOOD_BLOCKS_INSTALLER.value)
    recommendations.append(RescueRecommendationCodeV2.REVIEW_PCIE_AER.value)

  if RescueIssueCodeV2.PCIE_NOAER_LIMITATION.value in issues:
    codes.append(RescueIssueCodeV2.PCIE_NOAER_LIMITATION.value)

  bios = bios_compare or {}
  if bios.get("status") in {"outdated", "newer_available"} or bios.get("outdated") is True:
    codes.append(RescueIssueCodeV2.BIOS_OUTDATED_LIKELY.value)
    recommendations.append(RescueRecommendationCodeV2.GUIDED_BIOS_SESSION.value)

  if secure_boot and secure_boot.lower() in {"enabled", "on"}:
    codes.append(RescueIssueCodeV2.SECURE_BOOT_BLOCKS_UNSIGNED_ISO.value)

  if iso_sha256_ok is False:
    codes.append(RescueIssueCodeV2.INSTALL_ISO_HASH_MISMATCH.value)

  if nvme_count >= 2 and not disk_roles_bound:
    codes.append(RescueIssueCodeV2.NVME_ROLE_BIND_REQUIRED.value)
    recommendations.append(RescueRecommendationCodeV2.BIND_DISK_ROLES.value)

  if not codes:
    codes.append(RescueIssueCodeV2.INSTALL_DIAGNOSIS_CLEAR.value)

  severity = "info"
  if any(
    c
    in {
      RescueIssueCodeV2.BIOS_OUTDATED_LIKELY.value,
      RescueIssueCodeV2.PCIE_AER_FLOOD_BLOCKS_INSTALLER.value,
      RescueIssueCodeV2.INSTALL_ISO_HASH_MISMATCH.value,
    }
    for c in codes
  ):
    severity = "high"

  return {
    "schema_version": DIAGNOSIS_SCHEMA,
    "severity": severity,
    "issue_codes": sorted(set(codes)),
    "recommendation_codes": sorted(set(recommendations)),
    "next_action": _next_action(codes),
    "orchestration": "dev_laptop",
    "cloud_telemetry_useful": True,
    "cloud_diagnostics_useful": True,
  }


def _next_action(codes: list[str]) -> str:
  if RescueIssueCodeV2.BIOS_OUTDATED_LIKELY.value in codes:
    return "guided_bios_session_or_continue_with_operator_risk_ack"
  if RescueIssueCodeV2.NVME_ROLE_BIND_REQUIRED.value in codes:
    return "bind_disk_roles"
  if RescueIssueCodeV2.INSTALL_ISO_HASH_MISMATCH.value in codes:
    return "reverify_or_redownload_iso"
  if RescueIssueCodeV2.PCIE_AER_FLOOD_BLOCKS_INSTALLER.value in codes:
    return "use_msi_compat_boot_and_review_aer"
  return "proceed_mint_plan_dry_run"
