"""
Rescue recommendation codes V2 — read-only advice identifiers for operators.
"""

from __future__ import annotations

from enum import Enum


class RescueRecommendationCodeV2(str, Enum):
  EXPLAIN_ONLY = "explain_only"
  CHECK_FIRMWARE_PACKAGES = "check_firmware_packages"
  INSTALL_FIRMWARE_NONFREE = "install_firmware_nonfree_review"
  ENABLE_WIFI_RADIO = "enable_wifi_radio"
  UNBLOCK_RFKILL = "unblock_rfkill"
  RESCAN_WIFI = "rescan_wifi"
  RESTART_NETWORK_MANAGER_LIVE = "restart_network_manager_live"
  CHECK_DNS = "check_dns"
  CHECK_HTTPS_CONNECTIVITY = "check_https_connectivity"
  CONFIGURE_TELEMETRY_ENDPOINT = "configure_telemetry_endpoint"
  RETRY_TELEMETRY_QUEUE = "retry_telemetry_queue"
  REVIEW_STORAGE_SMART = "review_storage_smart"
  REVIEW_NVME_HEALTH = "review_nvme_health"
  USE_EXTERNAL_BACKUP_TARGET = "use_external_backup_target"
  REVIEW_PCIE_AER = "review_pcie_aer"
  OPERATOR_CONFIRM_LOW_RISK_FIX = "operator_confirm_low_risk_fix"
  DESTRUCTIVE_BLOCKED_MANUAL_GUIDE = "destructive_blocked_manual_guide"
  BETA_AGREEMENT_REQUIRED = "beta_agreement_required"
  DEVICE_APPROVAL_REQUIRED = "device_approval_required"
  STICK_VERIFICATION_REQUIRED = "stick_verification_required"


SAFE_RECOMMENDATION_CODES: frozenset[str] = frozenset(
  {
    RescueRecommendationCodeV2.EXPLAIN_ONLY.value,
    RescueRecommendationCodeV2.RESTART_NETWORK_MANAGER_LIVE.value,
    RescueRecommendationCodeV2.UNBLOCK_RFKILL.value,
    RescueRecommendationCodeV2.RESCAN_WIFI.value,
    RescueRecommendationCodeV2.RETRY_TELEMETRY_QUEUE.value,
  }
)


def recommendation_code_values() -> frozenset[str]:
  return frozenset(c.value for c in RescueRecommendationCodeV2)
