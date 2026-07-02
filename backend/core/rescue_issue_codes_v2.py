"""
Rescue system assessment issue codes V2 — stable identifiers for hardware/network/storage problems.
"""

from __future__ import annotations

from enum import Enum


class RescueIssueCodeV2(str, Enum):
  # System
  MISSING_TOOL = "missing_tool"
  BIOS_INFO_UNAVAILABLE = "bios_info_unavailable"
  SECURE_BOOT_UNKNOWN = "secure_boot_unknown"

  # CPU/RAM
  CPU_INFO_PARTIAL = "cpu_info_partial"
  RAM_SIZE_UNKNOWN = "ram_size_unknown"

  # GPU
  GPU_DRIVER_MISSING = "gpu_driver_missing"
  GPU_FIRMWARE_HINT = "gpu_firmware_hint"
  NVIDIA_COMPAT_MODE = "nvidia_compat_mode"

  # Network
  NETWORK_LAN_UP = "network_lan_up"
  NETWORK_LAN_DOWN = "network_lan_down"
  NETWORK_WIFI_CONNECTED = "network_wifi_connected"
  NETWORK_WIFI_UNCONNECTED = "network_wifi_unconnected"
  NETWORK_WIFI_BLOCKED_BY_LAN_REGRESSION = "network_wifi_blocked_by_lan_regression"
  DNS_OK = "dns_ok"
  DNS_FAILED = "dns_failed"
  HTTPS_OK = "https_ok"
  HTTPS_FAILED = "https_failed"
  TELEMETRY_DEV_LAPTOP_REACHABLE = "telemetry_dev_laptop_reachable"
  TELEMETRY_BETA_SERVER_REACHABLE = "telemetry_beta_server_reachable"
  TELEMETRY_ENDPOINT_UNREACHABLE = "telemetry_endpoint_unreachable"
  TELEMETRY_NOT_CONFIGURED = "telemetry_not_configured"
  FIRMWARE_WIFI_MISSING = "firmware_wifi_missing"
  RFKILL_BLOCKED = "rfkill_blocked"

  # Storage
  STORAGE_SMART_WARNING = "storage_smart_warning"
  STORAGE_NVME_WARNING = "storage_nvme_warning"
  STORAGE_BACKUP_TARGET_POOR = "storage_backup_target_poor"
  PARTITION_TABLE_UNKNOWN = "partition_table_unknown"

  # PCIe/AER
  PCIE_AER_CORRECTED = "pcie_aer_corrected"
  PCIE_AER_NONFATAL = "pcie_aer_nonfatal"
  PCIE_AER_FATAL = "pcie_aer_fatal"
  PCIE_NOAER_LIMITATION = "pcie_noaer_limitation"

  # Firmware/drivers
  DMESG_FIRMWARE_MISSING = "dmesg_firmware_missing"
  DRIVER_MISSING = "driver_missing"
  PACKAGE_COVERAGE_GAP = "package_coverage_gap"

  # Malware/manipulation (read-only hints)
  SUSPICIOUS_AUTOSTART_HINT = "suspicious_autostart_hint"
  SUSPICIOUS_WEBROOT_HINT = "suspicious_webroot_hint"


ISSUE_SEVERITY: dict[str, str] = {
  RescueIssueCodeV2.PCIE_AER_FATAL.value: "critical",
  RescueIssueCodeV2.PCIE_AER_NONFATAL.value: "high",
  RescueIssueCodeV2.STORAGE_SMART_WARNING.value: "high",
  RescueIssueCodeV2.STORAGE_NVME_WARNING.value: "high",
  RescueIssueCodeV2.DNS_FAILED.value: "medium",
  RescueIssueCodeV2.HTTPS_FAILED.value: "medium",
  RescueIssueCodeV2.TELEMETRY_ENDPOINT_UNREACHABLE.value: "medium",
  RescueIssueCodeV2.MISSING_TOOL.value: "low",
}


def issue_code_values() -> frozenset[str]:
  return frozenset(c.value for c in RescueIssueCodeV2)
