"""
SATA/SAS SSD baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 8.

Attribute-level ``smartctl`` parsing tuned for non-rotational SATA/SAS SSDs:
wear leveling, reserved/spare block space, reported uncorrectable errors,
UDMA CRC errors, unsafe shutdown count, plus TRIM support detection. SMART
attribute *IDs* used here are the common cross-vendor convention but are
not universal — unknown/vendor-specific attribute layouts are simply
absent from the parsed table, never guessed. Never starts a SMART self-test.
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from core.hardware_baseline_contracts import (
    BaselineSeverity,
    BaselineStatus,
    BaselineSubsystem,
    ExtendedTestRecommendation,
    HardwareFinding,
    HardwareMetric,
    HardwareSubsystemResult,
    _utc_now,
)
from core.hdd_baseline_diagnostics import parse_smartctl_attributes, parse_smartctl_overall_health
from core.storage_baseline_diagnostics import scan_kernel_storage_errors

SATA_SSD_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_ATTR_REALLOCATED_SECTOR_CT = 5
_ATTR_WEAR_LEVELING_COUNT = 177
_ATTR_AVAILABLE_RESERVD_SPACE = 232
_ATTR_REPORTED_UNCORRECT = 187
_ATTR_UDMA_CRC_ERROR_COUNT = 199
_ATTR_UNEXPECT_POWER_LOSS_CT = 174

_WEAR_LEVELING_WARNING_VALUE = 10
_RESERVED_SPACE_CRITICAL_VALUE = 10
_UNSAFE_SHUTDOWN_WARNING_COUNT = 5
_REPEATED_IO_ERROR_THRESHOLD = 3


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 30) -> tuple[str, bool]:
    try:
        if runner is not None:
            result = runner(argv, capture_output=True, text=True, timeout=timeout)
        else:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)  # noqa: S603
        return (result.stdout or ""), True
    except FileNotFoundError:
        return "", False
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return "", False


def detect_trim_support(device_name: str, *, sysfs_root: Path | None = None) -> bool | None:
    """True/False from ``queue/discard_granularity``; ``None`` when the
    sysfs entry is absent (never guess TRIM support)."""
    root = sysfs_root or Path("/")
    path = root / "sys" / "block" / device_name / "queue" / "discard_granularity"
    try:
        if not path.exists():
            return None
        return int(path.read_text(encoding="utf-8", errors="ignore").strip()) > 0
    except (OSError, ValueError):
        return None


def build_sata_ssd_baseline_result(
    *,
    device_id: str,
    smart_health_raw: str | None = None,
    smart_attributes_raw: str | None = None,
    smartctl_available: bool = True,
    dmesg_text: str | None = None,
    sysfs_root: Path | None = None,
    runner: Runner = None,
) -> HardwareSubsystemResult:
    started_at = _utc_now()
    t0 = time.monotonic()

    checks_run: list[str] = []
    checks_skipped: list[str] = []
    findings: list[HardwareFinding] = []
    metrics: list[HardwareMetric] = []
    recommendations: list[str] = []

    health_text = smart_health_raw
    attrs_text = smart_attributes_raw
    dev_path = device_id if device_id.startswith("/dev/") else f"/dev/{device_id}"

    if smartctl_available and health_text is None:
        health_text, present = _run_tool(["smartctl", "-H", dev_path], runner=runner)
        if not present:
            smartctl_available = False
    if smartctl_available and attrs_text is None:
        attrs_text, present = _run_tool(["smartctl", "-A", dev_path], runner=runner)
        if not present:
            smartctl_available = False

    if not smartctl_available:
        checks_skipped.append("smartctl")
    else:
        checks_run.append("smart_overall_health")
        checks_run.append("smart_attribute_table")

        overall = parse_smartctl_overall_health(health_text or "")
        metrics.append(HardwareMetric(name="smart_overall_health", value=overall))
        if overall == "FAILED":
            findings.append(
                HardwareFinding(code="sata_ssd.smart_overall_failed", severity=BaselineSeverity.RED.value, message="SMART overall-health self-assessment reports FAILED.")
            )

        attrs = parse_smartctl_attributes(attrs_text or "")
        wear = attrs.get(_ATTR_WEAR_LEVELING_COUNT)
        reserved = attrs.get(_ATTR_AVAILABLE_RESERVD_SPACE)
        uncorrect = attrs.get(_ATTR_REPORTED_UNCORRECT)
        crc = attrs.get(_ATTR_UDMA_CRC_ERROR_COUNT)
        unsafe_shutdown = attrs.get(_ATTR_UNEXPECT_POWER_LOSS_CT)

        if wear is not None:
            metrics.append(HardwareMetric(name="wear_leveling_value", value=wear["value"]))
            if wear["value"] <= _WEAR_LEVELING_WARNING_VALUE:
                findings.append(
                    HardwareFinding(code="sata_ssd.wear_warning", severity=BaselineSeverity.YELLOW.value, message=f"Wear leveling attribute value is {wear['value']} (<= {_WEAR_LEVELING_WARNING_VALUE}).")
                )
        if reserved is not None:
            metrics.append(HardwareMetric(name="available_reserved_space_value", value=reserved["value"]))
            if reserved["value"] <= _RESERVED_SPACE_CRITICAL_VALUE:
                findings.append(
                    HardwareFinding(code="sata_ssd.low_reserved_space", severity=BaselineSeverity.RED.value, message=f"Available reserved space attribute value is {reserved['value']} (<= {_RESERVED_SPACE_CRITICAL_VALUE}).")
                )
        if uncorrect is not None and uncorrect["raw_value"] > 0:
            metrics.append(HardwareMetric(name="reported_uncorrect", value=uncorrect["raw_value"]))
            findings.append(
                HardwareFinding(code="sata_ssd.uncorrectable_errors_detected", severity=BaselineSeverity.RED.value, message=f"{uncorrect['raw_value']} reported uncorrectable error(s).")
            )
        if crc is not None and crc["raw_value"] > 0:
            metrics.append(HardwareMetric(name="udma_crc_error_count", value=crc["raw_value"]))
            findings.append(
                HardwareFinding(code="sata_ssd.crc_error_detected", severity=BaselineSeverity.YELLOW.value, message=f"{crc['raw_value']} UDMA CRC error(s) reported (often a cable/connection issue).")
            )
        if unsafe_shutdown is not None and unsafe_shutdown["raw_value"] >= _UNSAFE_SHUTDOWN_WARNING_COUNT:
            metrics.append(HardwareMetric(name="unexpected_power_loss_count", value=unsafe_shutdown["raw_value"]))
            findings.append(
                HardwareFinding(code="sata_ssd.unsafe_shutdowns_detected", severity=BaselineSeverity.YELLOW.value, message=f"{unsafe_shutdown['raw_value']} unexpected power-loss event(s) recorded.")
            )

    checks_run.append("trim_support_detection")
    trim_supported = detect_trim_support(device_id.replace("/dev/", ""), sysfs_root=sysfs_root)
    if trim_supported is None:
        checks_skipped.append("trim_support_detection:sysfs_entry_missing")
    else:
        metrics.append(HardwareMetric(name="trim_supported", value=trim_supported))

    checks_run.append("kernel_io_error_scan")
    kernel_scan = scan_kernel_storage_errors(device_id, dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    metrics.append(HardwareMetric(name="kernel_io_error_count", value=kernel_scan["io_error_count"]))
    if kernel_scan["io_error_count"] >= _REPEATED_IO_ERROR_THRESHOLD:
        findings.append(
            HardwareFinding(code="sata_ssd.repeated_io_errors", severity=BaselineSeverity.RED.value, message=f"{kernel_scan['io_error_count']} I/O error(s) for this device found in kernel log.")
        )

    has_red = any(f.severity == BaselineSeverity.RED.value for f in findings)
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)

    extended_test = ExtendedTestRecommendation()
    if has_red:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(recommended=True, required=True, test_type="smart_self_test_extended", estimated_duration="under_2_hours")
        recommendations.append("Back up this SSD's data before any further use; do not use it as a restore/OS-install target.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="smart_self_test_short", estimated_duration="under_1_hour")
        recommendations.append("Monitor wear/CRC trend; consider a SMART short self-test.")
    elif not smartctl_available:
        status = BaselineStatus.TEST_UNAVAILABLE.value
        severity = BaselineSeverity.GRAY.value
    else:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.SATA_SSD.value,
        status=status,
        severity=severity,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        checks_run=tuple(checks_run),
        checks_skipped=tuple(checks_skipped),
        metrics=tuple(metrics),
        findings=tuple(findings),
        recommendations=tuple(recommendations),
        extended_test=extended_test,
        device_id=device_id,
    )


def build_sata_ssd_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": SATA_SSD_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.sata_ssd_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "starts_smart_self_test": False,
    }


__all__ = [
    "SATA_SSD_BASELINE_DIAGNOSTICS_VERSION",
    "detect_trim_support",
    "build_sata_ssd_baseline_result",
    "build_sata_ssd_baseline_diagnostics",
]
