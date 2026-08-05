"""
NVMe baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 9.

Parses ``nvme smart-log`` (critical warning bits, available spare vs.
threshold, percentage used, media errors, unsafe shutdowns, temperature)
and ``nvme id-ctrl`` (firmware version, namespace count). Distinguishes a
genuinely empty/unparseable SMART log (common on USB-NVMe bridges that do
not pass SMART through) from a real all-zero/healthy log. Kernel error
scanning matches the *controller* name (``nvme0``), not the *namespace*
block device (``nvme0n1``) — kernel messages almost always name the
controller. Never starts a SMART self-test or firmware update.
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

NVME_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_HIGH_TEMPERATURE_C = 70
_PERCENTAGE_USED_WARNING = 80
_PERCENTAGE_USED_CRITICAL = 100
_UNSAFE_SHUTDOWN_WARNING_COUNT = 20
_REPEATED_IO_ERROR_THRESHOLD = 3
_REPEATED_RESET_THRESHOLD = 2


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


def nvme_controller_name(device_id: str) -> str:
    """``nvme0n1`` -> ``nvme0`` (strip namespace suffix). Kernel log
    messages name the controller, not the namespace block device."""
    m = re.match(r"^(nvme\d+)", device_id.replace("/dev/", ""))
    return m.group(1) if m else device_id.replace("/dev/", "")


def parse_nvme_smart_log(text: str) -> dict[str, Any]:
    """Parse ``nvme smart-log`` key/value output. Every field is ``None``
    when absent — never fabricated."""

    def _find_int(pattern: str) -> int | None:
        m = re.search(pattern, text or "", re.IGNORECASE)
        if not m:
            return None
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None

    critical_warning = _find_int(r"Critical Warning:\s*(?:0x)?([0-9a-fA-F]+)")
    return {
        "critical_warning": critical_warning,
        "temperature_c": _find_int(r"Temperature:\s*(\d+)\s*C"),
        "available_spare_pct": _find_int(r"Available Spare:\s*(\d+)%"),
        "available_spare_threshold_pct": _find_int(r"Available Spare Threshold:\s*(\d+)%"),
        "percentage_used_pct": _find_int(r"Percentage Used:\s*(\d+)%"),
        "unsafe_shutdowns": _find_int(r"Unsafe Shutdowns:\s*([\d,]+)"),
        "media_errors": _find_int(r"Media and Data Integrity Errors:\s*([\d,]+)"),
    }


def parse_nvme_id_ctrl(text: str) -> dict[str, Any]:
    """Parse ``nvme id-ctrl`` firmware revision (``fr``) and namespace
    count (``nn``)."""
    fr_m = re.search(r"^fr\s*:\s*(\S+)", text or "", re.MULTILINE)
    nn_m = re.search(r"^nn\s*:\s*(\d+)", text or "", re.MULTILINE)
    return {
        "firmware_version": fr_m.group(1) if fr_m else None,
        "namespace_count": int(nn_m.group(1)) if nn_m else None,
    }


def build_nvme_baseline_result(
    *,
    device_id: str,
    smart_log_raw: str | None = None,
    id_ctrl_raw: str | None = None,
    nvme_cli_available: bool = True,
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

    dev_path = device_id if device_id.startswith("/dev/") else f"/dev/{device_id}"
    smart_text = smart_log_raw
    ctrl_text = id_ctrl_raw

    if nvme_cli_available and smart_text is None:
        smart_text, present = _run_tool(["nvme", "smart-log", dev_path], runner=runner)
        if not present:
            nvme_cli_available = False
    if nvme_cli_available and ctrl_text is None:
        ctrl_text, present = _run_tool(["nvme", "id-ctrl", dev_path], runner=runner)
        if not present:
            nvme_cli_available = False

    if not nvme_cli_available:
        checks_skipped.append("nvme-cli")
    else:
        checks_run.append("nvme_smart_log")
        checks_run.append("nvme_id_ctrl")

        smart = parse_nvme_smart_log(smart_text or "")
        smart_has_any_data = any(v is not None for v in smart.values())

        ctrl = parse_nvme_id_ctrl(ctrl_text or "")
        if ctrl.get("firmware_version"):
            metrics.append(HardwareMetric(name="firmware_version", value=ctrl["firmware_version"]))
        if ctrl.get("namespace_count") is not None:
            metrics.append(HardwareMetric(name="namespace_count", value=ctrl["namespace_count"]))

        if not smart_has_any_data:
            findings.append(
                HardwareFinding(
                    code="nvme.incomplete_smart_log",
                    severity=BaselineSeverity.GRAY.value,
                    message="NVMe SMART log could not be parsed (empty or unsupported — common on USB-NVMe bridges).",
                )
            )
        else:
            for key in ("critical_warning", "temperature_c", "available_spare_pct", "available_spare_threshold_pct", "percentage_used_pct", "unsafe_shutdowns", "media_errors"):
                if smart.get(key) is not None:
                    metrics.append(HardwareMetric(name=key, value=smart[key]))

            if smart.get("critical_warning") and smart["critical_warning"] != 0:
                findings.append(
                    HardwareFinding(code="nvme.critical_warning", severity=BaselineSeverity.RED.value, message=f"Critical Warning bitmask is non-zero (0x{smart['critical_warning']:x}).")
                )
            spare = smart.get("available_spare_pct")
            spare_threshold = smart.get("available_spare_threshold_pct")
            if spare is not None and spare_threshold is not None and spare <= spare_threshold:
                findings.append(
                    HardwareFinding(code="nvme.low_available_spare", severity=BaselineSeverity.RED.value, message=f"Available spare {spare}% is at or below threshold {spare_threshold}%.")
                )
            used = smart.get("percentage_used_pct")
            if used is not None:
                if used >= _PERCENTAGE_USED_CRITICAL:
                    findings.append(
                        HardwareFinding(code="nvme.high_percentage_used", severity=BaselineSeverity.RED.value, message=f"Percentage used is {used}% (>= {_PERCENTAGE_USED_CRITICAL}%).")
                    )
                elif used >= _PERCENTAGE_USED_WARNING:
                    findings.append(
                        HardwareFinding(code="nvme.high_percentage_used", severity=BaselineSeverity.YELLOW.value, message=f"Percentage used is {used}% (>= {_PERCENTAGE_USED_WARNING}%).")
                    )
            media_errors = smart.get("media_errors")
            if media_errors and media_errors > 0:
                findings.append(
                    HardwareFinding(code="nvme.media_errors_detected", severity=BaselineSeverity.RED.value, message=f"{media_errors} media/data-integrity error(s) reported.")
                )
            temp = smart.get("temperature_c")
            if temp is not None and temp >= _HIGH_TEMPERATURE_C:
                findings.append(
                    HardwareFinding(code="nvme.high_temperature", severity=BaselineSeverity.YELLOW.value, message=f"Reported temperature {temp}\u00b0C >= {_HIGH_TEMPERATURE_C}\u00b0C.")
                )
            unsafe = smart.get("unsafe_shutdowns")
            if unsafe is not None and unsafe >= _UNSAFE_SHUTDOWN_WARNING_COUNT:
                findings.append(
                    HardwareFinding(code="nvme.unsafe_shutdowns_detected", severity=BaselineSeverity.YELLOW.value, message=f"{unsafe} unsafe shutdown(s) recorded.")
                )

    checks_run.append("kernel_controller_error_scan")
    controller_name = nvme_controller_name(device_id)
    kernel_scan = scan_kernel_storage_errors(controller_name, dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    metrics.append(HardwareMetric(name="kernel_io_error_count", value=kernel_scan["io_error_count"]))
    metrics.append(HardwareMetric(name="kernel_reset_timeout_count", value=kernel_scan["reset_timeout_count"]))

    if kernel_scan["reset_timeout_count"] >= _REPEATED_RESET_THRESHOLD:
        findings.append(
            HardwareFinding(code="nvme.repeated_controller_resets", severity=BaselineSeverity.RED.value, message=f"{kernel_scan['reset_timeout_count']} controller reset/timeout event(s) found in kernel log.")
        )
    elif kernel_scan["io_error_count"] >= _REPEATED_IO_ERROR_THRESHOLD:
        findings.append(
            HardwareFinding(code="nvme.repeated_io_errors", severity=BaselineSeverity.RED.value, message=f"{kernel_scan['io_error_count']} I/O error(s) for this controller found in kernel log.")
        )

    has_red = any(f.severity == BaselineSeverity.RED.value for f in findings)
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)
    has_gray_only = any(f.severity == BaselineSeverity.GRAY.value for f in findings) and not has_red and not has_yellow

    extended_test = ExtendedTestRecommendation()
    if has_red:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(recommended=True, required=True, test_type="smart_self_test_extended", estimated_duration="under_1_hour")
        recommendations.append("Back up this NVMe drive's data before any further use; do not use it as a restore/OS-install target.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="smart_self_test_short", estimated_duration="under_30_minutes")
        recommendations.append("Monitor wear/temperature trend; consider a SMART short self-test.")
    elif has_gray_only or not nvme_cli_available:
        status = BaselineStatus.TEST_UNAVAILABLE.value
        severity = BaselineSeverity.GRAY.value
    else:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.NVME.value,
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


def build_nvme_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": NVME_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.nvme_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "starts_smart_self_test": False,
        "triggers_firmware_update": False,
    }


__all__ = [
    "NVME_BASELINE_DIAGNOSTICS_VERSION",
    "nvme_controller_name",
    "parse_nvme_smart_log",
    "parse_nvme_id_ctrl",
    "build_nvme_baseline_result",
    "build_nvme_baseline_diagnostics",
]
