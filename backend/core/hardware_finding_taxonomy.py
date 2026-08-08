"""
Map hardware baseline finding codes to diagnostics/telemetry taxonomy.

PI-RS-ASUS-ROOTCAUSE-006B — EXPECTED STATE vs FAILURE for server-side diagnosis.
"""

from __future__ import annotations

from typing import Any

HARDWARE_FINDING_TAXONOMY_VERSION = 1

_CODE_TO_TYPE = {
    "memory.mce_decoder_enabled": "hardware.informational_kernel_event",
    "cpu.mce_decoder_enabled": "hardware.informational_kernel_event",
    "gpu.expected_reset": "hardware.informational_kernel_event",
    "gpu.driver_intentionally_disabled": "hardware.expected_profile_state",
    "gpu.disabled_by_cmdline": "hardware.expected_profile_state",
    "memory.kernel_corrected_mce": "hardware.degraded",
    "cpu.machine_check_corrected": "hardware.degraded",
    "memory.kernel_uncorrected_error": "hardware.actual_failure",
    "cpu.machine_check_detected": "hardware.actual_failure",
    "gpu.kernel_error_detected": "hardware.actual_failure",
    "gpu.driver_missing": "hardware.degraded",
}


def classify_hardware_finding_for_telemetry(
    *,
    code: str,
    severity: str | None = None,
    category: str | None = None,
    action_blocking: bool | None = None,
) -> dict[str, Any]:
    """Return a compact taxonomy record for cloud/diagnostics forwarding."""
    finding_type = _CODE_TO_TYPE.get(code)
    if finding_type is None:
        if category == "expected_by_profile":
            finding_type = "hardware.expected_profile_state"
        elif category == "informational":
            finding_type = "hardware.informational_kernel_event"
        elif category == "critical" or severity == "red":
            finding_type = "hardware.actual_failure"
        elif category in ("warning", "degraded") or severity == "yellow":
            finding_type = "hardware.degraded"
        else:
            finding_type = "hardware.informational_kernel_event"

    next_test = None
    if code == "gpu.driver_intentionally_disabled":
        next_test = "not_required_for_tui_baseline"
    elif code in ("memory.kernel_uncorrected_error", "cpu.machine_check_detected"):
        next_test = "memtest_or_vendor_uefi_diag"
    elif code == "gpu.kernel_error_detected":
        next_test = "supervised_gpu_render_stress"

    return {
        "taxonomy_version": HARDWARE_FINDING_TAXONOMY_VERSION,
        "issue_code": code,
        "finding_type": finding_type,
        "severity": severity,
        "category": category,
        "action_blocking": action_blocking,
        "next_test": next_test,
    }


__all__ = [
    "HARDWARE_FINDING_TAXONOMY_VERSION",
    "classify_hardware_finding_for_telemetry",
]
