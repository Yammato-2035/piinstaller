"""
HDD (rotational) baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 7.

Attribute-level ``smartctl`` parsing for spinning disks, going beyond a
simple SMART PASSED/FAILED summary: pending sectors, offline uncorrectable
sectors, reallocated sectors, UDMA CRC errors, temperature. Combined with
the shared kernel I/O-error scan from ``storage_baseline_diagnostics``.
Never starts a SMART self-test (``smartctl -t``) — only reads existing
attribute tables.
"""

from __future__ import annotations

import re
import subprocess
import time
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
from core.storage_baseline_diagnostics import scan_kernel_storage_errors

HDD_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_HIGH_TEMPERATURE_C = 55
_REPEATED_IO_ERROR_THRESHOLD = 3

# SMART attribute IDs relevant to rotational disks (name kept for readability;
# ID is the authoritative match since vendors vary attribute *names* slightly).
_ATTR_REALLOCATED_SECTOR_CT = 5
_ATTR_CURRENT_PENDING_SECTOR = 197
_ATTR_OFFLINE_UNCORRECTABLE = 198
_ATTR_UDMA_CRC_ERROR_COUNT = 199
_ATTR_TEMPERATURE_CELSIUS = 194


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


def parse_smartctl_overall_health(text: str) -> str | None:
    """"PASSED"|"FAILED"|None (None when the line is absent, e.g. USB
    bridges that do not pass SMART through)."""
    m = re.search(r"SMART overall-health self-assessment test result:\s*(\w+)", text or "")
    if not m:
        return None
    return m.group(1).upper()


_ATTRIBUTE_LINE_RE = re.compile(
    r"^\s*(\d+)\s+(\S+)\s+[\w-]+\s+(\d+)\s+(\d+)\s+(\d+|---)\s+\S+\s+\S+\s+\S+\s+(\d+)"
)


def parse_smartctl_attributes(text: str) -> dict[int, dict[str, Any]]:
    """Parse the classic ``-A`` attribute table
    (``ID# ATTRIBUTE_NAME FLAG VALUE WORST THRESH TYPE UPDATED WHEN_FAILED RAW_VALUE``)
    into ``{attribute_id: {...}}``. Trailing raw-value annotations (e.g.
    ``"0h+05m+00.000s"`` for power-on-hours-style attributes) are ignored —
    only the leading integer is captured."""
    attrs: dict[int, dict[str, Any]] = {}
    for line in (text or "").splitlines():
        m = _ATTRIBUTE_LINE_RE.match(line)
        if not m:
            continue
        attr_id = int(m.group(1))
        attrs[attr_id] = {
            "name": m.group(2),
            "value": int(m.group(3)),
            "worst": int(m.group(4)),
            "threshold": None if m.group(5) == "---" else int(m.group(5)),
            "raw_value": int(m.group(6)),
        }
    return attrs


def build_hdd_baseline_result(
    *,
    device_id: str,
    smart_health_raw: str | None = None,
    smart_attributes_raw: str | None = None,
    smartctl_available: bool = True,
    dmesg_text: str | None = None,
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
                HardwareFinding(code="hdd.smart_overall_failed", severity=BaselineSeverity.RED.value, message="SMART overall-health self-assessment reports FAILED.")
            )

        attrs = parse_smartctl_attributes(attrs_text or "")
        pending = attrs.get(_ATTR_CURRENT_PENDING_SECTOR)
        offline_unc = attrs.get(_ATTR_OFFLINE_UNCORRECTABLE)
        realloc = attrs.get(_ATTR_REALLOCATED_SECTOR_CT)
        crc = attrs.get(_ATTR_UDMA_CRC_ERROR_COUNT)
        temp = attrs.get(_ATTR_TEMPERATURE_CELSIUS)

        if pending and pending["raw_value"] > 0:
            metrics.append(HardwareMetric(name="current_pending_sector", value=pending["raw_value"]))
            findings.append(
                HardwareFinding(code="hdd.pending_sectors_detected", severity=BaselineSeverity.RED.value, message=f"{pending['raw_value']} pending sector(s) reported.")
            )
        if offline_unc and offline_unc["raw_value"] > 0:
            metrics.append(HardwareMetric(name="offline_uncorrectable", value=offline_unc["raw_value"]))
            findings.append(
                HardwareFinding(code="hdd.offline_uncorrectable_detected", severity=BaselineSeverity.RED.value, message=f"{offline_unc['raw_value']} offline-uncorrectable sector(s) reported.")
            )
        if realloc and realloc["raw_value"] > 0:
            metrics.append(HardwareMetric(name="reallocated_sector_ct", value=realloc["raw_value"]))
            findings.append(
                HardwareFinding(code="hdd.reallocated_sectors_detected", severity=BaselineSeverity.YELLOW.value, message=f"{realloc['raw_value']} reallocated sector(s) reported.")
            )
        if crc and crc["raw_value"] > 0:
            metrics.append(HardwareMetric(name="udma_crc_error_count", value=crc["raw_value"]))
            findings.append(
                HardwareFinding(code="hdd.crc_error_detected", severity=BaselineSeverity.YELLOW.value, message=f"{crc['raw_value']} UDMA CRC error(s) reported (often a cable/connection issue).")
            )
        if temp and temp["raw_value"] >= _HIGH_TEMPERATURE_C:
            metrics.append(HardwareMetric(name="temperature_celsius", value=temp["raw_value"], unit="C"))
            findings.append(
                HardwareFinding(code="hdd.high_temperature", severity=BaselineSeverity.YELLOW.value, message=f"Reported temperature {temp['raw_value']}\u00b0C >= {_HIGH_TEMPERATURE_C}\u00b0C.")
            )
        elif temp:
            metrics.append(HardwareMetric(name="temperature_celsius", value=temp["raw_value"], unit="C"))

    checks_run.append("kernel_io_error_scan")
    kernel_scan = scan_kernel_storage_errors(device_id, dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    metrics.append(HardwareMetric(name="kernel_io_error_count", value=kernel_scan["io_error_count"]))
    metrics.append(HardwareMetric(name="kernel_reset_timeout_count", value=kernel_scan["reset_timeout_count"]))

    if kernel_scan["io_error_count"] >= _REPEATED_IO_ERROR_THRESHOLD:
        findings.append(
            HardwareFinding(code="hdd.repeated_io_errors", severity=BaselineSeverity.RED.value, message=f"{kernel_scan['io_error_count']} I/O error(s) for this device found in kernel log.")
        )

    has_red = any(f.severity == BaselineSeverity.RED.value for f in findings)
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)

    extended_test = ExtendedTestRecommendation()
    if has_red:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(recommended=True, required=True, test_type="smart_self_test_extended", estimated_duration="several_hours")
        recommendations.append("Back up this disk's data before any further use; do not use it as a restore/OS-install target.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="smart_self_test_short", estimated_duration="under_2_hours")
        recommendations.append("Consider a SMART short self-test to confirm this is not progressing.")
    elif not smartctl_available:
        status = BaselineStatus.TEST_UNAVAILABLE.value
        severity = BaselineSeverity.GRAY.value
    else:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.HDD.value,
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


def build_hdd_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": HDD_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.hdd_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "starts_smart_self_test": False,
    }


__all__ = [
    "HDD_BASELINE_DIAGNOSTICS_VERSION",
    "parse_smartctl_overall_health",
    "parse_smartctl_attributes",
    "build_hdd_baseline_result",
    "build_hdd_baseline_diagnostics",
]
