"""
Operator/cloud dashboard view-model for one ASUS rescue boot.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 12.

Presentation only — technical device status remains authoritative.
Never paints green for sent-but-unconfirmed telemetry or detected-only devices.
"""

from __future__ import annotations

from typing import Any, Mapping


_OKISH = frozenset({"operational", "operational_probe_passed", "stable", "driver_bound", "firmware_loaded"})


def _normalize_component_status(raw: str | None, *, telemetry_confirmed: bool = False) -> str:
    value = (raw or "unknown").strip().lower()
    allowed = {
        "detected",
        "driver_missing",
        "firmware_missing",
        "limited",
        "operational",
        "failed",
        "removed",
        "unknown",
    }
    if value not in allowed:
        if value in _OKISH:
            value = "operational"
        elif value in {"queued_offline", "sent"}:
            value = "limited"
        else:
            value = "unknown"
    # Do not upgrade to operational without confirmation rules applied by caller.
    if value == "operational" and not telemetry_confirmed and raw in {"sent", "queued_offline"}:
        return "limited"
    return value


def build_boot_dashboard_row(run: Mapping[str, Any]) -> dict[str, Any]:
    telemetry_status = str(run.get("telemetry_status") or "unknown")
    diagnostics_status = str(run.get("diagnostics_status") or "unknown")
    telemetry_confirmed = telemetry_status in {"delivered_confirmed", "accepted"}
    diagnostics_confirmed = diagnostics_status in {"confirmed", "partial"}

    def comp(key: str) -> str:
        return _normalize_component_status(run.get(key), telemetry_confirmed=telemetry_confirmed)

    row = {
        "asus_device_binding": run.get("asus_device_binding") or "unbound",
        "run_id": run.get("run_id"),
        "boot_attempt": run.get("boot_attempt"),
        "boot_profile": run.get("boot_profile"),
        "payload_version": run.get("payload_version"),
        "kernel": run.get("kernel_version"),
        "bios": run.get("bios_version"),
        "last_successful_boot_marker": run.get("last_successful_marker"),
        "first_failed_boot_marker": run.get("first_failed_marker"),
        "cpu": comp("cpu_status"),
        "ram": comp("ram_status"),
        "amd_gpu": comp("amd_gpu_status"),
        "nvidia_gpu": comp("nvidia_gpu_status"),
        "nvme_1": comp("nvme_1_status"),
        "nvme_2": comp("nvme_2_status"),
        "network": comp("network_status"),
        "usb": comp("usb_status"),
        "input_devices": comp("input_status"),
        "telemetry_status": telemetry_status if telemetry_status != "sent" or telemetry_confirmed else "limited",
        "diagnostics_status": diagnostics_status,
        "missing_drivers": list(run.get("missing_drivers") or []),
        "missing_firmware": list(run.get("missing_firmware") or []),
        "root_cause_confidence": run.get("root_cause_confidence"),
        "next_recommended_action": run.get("next_recommended_action"),
        "comparison_to_previous_boot": run.get("comparison_to_previous_boot") or {},
        "green_prohibited_reasons": [],
    }
    if telemetry_status in {"sent", "queued_offline"} and not telemetry_confirmed:
        row["green_prohibited_reasons"].append("telemetry_not_confirmed")
    if not diagnostics_confirmed:
        row["green_prohibited_reasons"].append("diagnostics_not_confirmed")
    for key in ("cpu", "ram", "amd_gpu", "nvidia_gpu", "nvme_1", "nvme_2"):
        if row[key] == "detected":
            row["green_prohibited_reasons"].append(f"{key}_detected_only")
    return row
