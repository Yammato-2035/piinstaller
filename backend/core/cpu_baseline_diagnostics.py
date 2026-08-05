"""
CPU baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 4.

Builds on ``core.cpu_platform_detection`` (CPU/SoC inventory, architecture,
virtualization, microcode, thermal *zone names*) — this module does not
re-parse ``lscpu``/``cpuinfo`` itself, it only adds:

1. kernel/machine-check error scan (``dmesg``)
2. thermal *temperature* reading + throttling detection (``collect_thermal_
   sources`` only lists zone names, never a numeric reading — this module
   adds that numeric read)
3. a bounded, deterministic quick CPU probe (never a stress-ng/Prime95-style
   long-running load)

Never installs stress-ng/Prime95, never triggers a microcode or BIOS update.
"""

from __future__ import annotations

import hashlib
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
from core.cpu_platform_detection import build_cpu_platform_details

CPU_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_QUICK_PROBE_DEFAULT_TIMEOUT_S = 5.0
_QUICK_PROBE_SKIP_TEMP_C = 90.0
_THERMAL_WARNING_TEMP_C = 85.0
_KNOWN_CRITICAL_TEMP_ZONE_TYPES = {"x86_pkg_temp", "cpu-thermal", "soc-thermal"}


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 10) -> tuple[str, bool]:
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


def scan_kernel_cpu_errors(dmesg_text: str | None = None, *, runner: Runner = None) -> dict[str, Any]:
    """Scan kernel log text for CPU machine-check/hardware-error/lockup/
    watchdog signals. Read-only; a missing ``dmesg`` never crashes this."""
    missing_tools: list[str] = []
    text = dmesg_text
    if text is None:
        text, present = _run_tool(["dmesg"], runner=runner)
        if not present:
            missing_tools.append("dmesg")
    text = text or ""

    machine_check = len(re.findall(r"mce:|Machine Check", text, re.IGNORECASE))
    hardware_error = len(re.findall(r"\[Hardware Error\]", text))
    soft_lockup = len(re.findall(r"soft lockup", text, re.IGNORECASE))
    hard_lockup = len(re.findall(r"hard lockup", text, re.IGNORECASE))
    watchdog = len(re.findall(r"watchdog.*(?:reset|bark|timeout)", text, re.IGNORECASE))
    corrected_hw_error = len(re.findall(r"corrected hardware error|CPU\d+: Core temperature above threshold", text, re.IGNORECASE))

    return {
        "machine_check_count": machine_check,
        "hardware_error_count": hardware_error,
        "soft_lockup_count": soft_lockup,
        "hard_lockup_count": hard_lockup,
        "watchdog_count": watchdog,
        "corrected_hardware_error_count": corrected_hw_error,
        "missing_tools": missing_tools,
    }


def read_thermal_zone_temperatures(*, sysfs_root: Path | None = None) -> list[dict[str, Any]]:
    """Read numeric temperatures for each thermal zone (millidegree C in
    sysfs, converted to whole degrees C). Distinct from ``core.cpu_platform_
    detection.collect_thermal_sources``, which only lists zone *names*."""
    root = sysfs_root or Path("/")
    base = root / "sys" / "class" / "thermal"
    if not base.exists():
        return []
    zones: list[dict[str, Any]] = []
    try:
        for zone_dir in sorted(base.glob("thermal_zone*")):
            type_path = zone_dir / "type"
            temp_path = zone_dir / "temp"
            zone_type = None
            temp_c = None
            try:
                if type_path.exists():
                    zone_type = type_path.read_text(encoding="utf-8", errors="ignore").strip()
                if temp_path.exists():
                    raw = temp_path.read_text(encoding="utf-8", errors="ignore").strip()
                    temp_c = int(raw) / 1000.0
            except (OSError, ValueError):
                continue
            zones.append({"type": zone_type, "temperature_c": temp_c})
    except OSError:
        pass
    return zones


def detect_thermal_throttling(dmesg_text: str | None) -> bool:
    text = dmesg_text or ""
    return bool(re.search(r"thermal throttl|CPU\d+: Core temperature above threshold.*throttl", text, re.IGNORECASE))


def _quick_probe_checksum(seed: int, iterations: int) -> str:
    """Deterministic integer/hash workload — validated against the known
    checksum for the given (seed, iterations) pair, never marketed as a
    performance benchmark."""
    h = hashlib.sha256()
    value = seed
    for _ in range(iterations):
        value = (value * 1103515245 + 12345) & 0xFFFFFFFF
        h.update(value.to_bytes(4, "little"))
    return h.hexdigest()


def run_quick_cpu_probe(
    *,
    max_temp_c: float | None,
    timeout_s: float = _QUICK_PROBE_DEFAULT_TIMEOUT_S,
    clock: Callable[[], float] | None = None,
    worker: Callable[[int, int], str] | None = None,
    force_result: str | None = None,
) -> dict[str, Any]:
    """Bounded, deterministic CPU quick probe. Skips when a thermal zone is
    already at/above ``_QUICK_PROBE_SKIP_TEMP_C`` (never load an already-hot
    CPU). ``force_result`` is test-only ("checksum_mismatch"/"timeout")."""
    if max_temp_c is not None and max_temp_c >= _QUICK_PROBE_SKIP_TEMP_C:
        return {"status": "skipped_high_temperature", "duration_ms": 0}

    _clock = clock or time.monotonic
    _worker = worker or _quick_probe_checksum
    seed, iterations = 42, 20000
    expected = _quick_probe_checksum(seed, iterations)

    start = _clock()
    if force_result == "timeout":
        return {"status": "timeout", "duration_ms": int(timeout_s * 1000)}

    actual = _worker(seed, iterations)
    elapsed_s = _clock() - start
    if elapsed_s > timeout_s:
        return {"status": "timeout", "duration_ms": int(elapsed_s * 1000)}

    if force_result == "checksum_mismatch" or actual != expected:
        return {"status": "checksum_mismatch", "duration_ms": int(elapsed_s * 1000)}
    return {"status": "success", "duration_ms": int(elapsed_s * 1000)}


def build_cpu_baseline_result(
    *,
    lscpu_raw: str | None = None,
    cpuinfo_raw: str | None = None,
    uname_machine_raw: str | None = None,
    device_tree_compatible: str | None = None,
    dmesg_text: str | None = None,
    sysfs_root: Path | None = None,
    runner: Runner = None,
    skip_quick_probe: bool = False,
    probe_worker: Callable[[int, int], str] | None = None,
    probe_clock: Callable[[], float] | None = None,
    force_probe_result: str | None = None,
) -> HardwareSubsystemResult:
    started_at = _utc_now()
    t0 = time.monotonic()

    checks_run: list[str] = ["cpu_platform_inventory"]
    checks_skipped: list[str] = []
    findings: list[HardwareFinding] = []
    metrics: list[HardwareMetric] = []
    recommendations: list[str] = []

    platform_details = build_cpu_platform_details(
        lscpu_raw=lscpu_raw,
        cpuinfo_raw=cpuinfo_raw,
        uname_machine_raw=uname_machine_raw,
        device_tree_compatible=device_tree_compatible,
        runner=runner,
        sysfs_root=sysfs_root,
    )
    checks_skipped.extend(f"cpu_inventory:{m}" for m in platform_details.get("missing_tools") or [])
    metrics.append(HardwareMetric(name="architecture", value=platform_details["architecture"]))
    metrics.append(HardwareMetric(name="virtualization_available", value=platform_details["virtualization_available"]))
    metrics.append(HardwareMetric(name="microcode_status", value=platform_details["microcode_status"]))
    metrics.append(HardwareMetric(name="is_raspberry_pi_soc", value=platform_details["is_raspberry_pi_soc"]))

    if platform_details["microcode_status"] == "unknown" and not platform_details["is_raspberry_pi_soc"]:
        findings.append(
            HardwareFinding(
                code="cpu.microcode_review_required",
                severity=BaselineSeverity.YELLOW.value,
                message="Microcode status could not be verified from /proc/cpuinfo.",
            )
        )

    checks_run.append("kernel_error_scan")
    kernel_scan = scan_kernel_cpu_errors(dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    for key in ("machine_check_count", "hardware_error_count", "soft_lockup_count", "hard_lockup_count", "watchdog_count"):
        metrics.append(HardwareMetric(name=key, value=kernel_scan[key]))

    if kernel_scan["machine_check_count"] > 0:
        findings.append(
            HardwareFinding(
                code="cpu.machine_check_detected",
                severity=BaselineSeverity.RED.value,
                message=f"{kernel_scan['machine_check_count']} machine-check event(s) found in kernel log.",
            )
        )
    if kernel_scan["hardware_error_count"] > 0 or kernel_scan["hard_lockup_count"] > 0 or kernel_scan["watchdog_count"] > 0:
        findings.append(
            HardwareFinding(
                code="cpu.hardware_error_detected",
                severity=BaselineSeverity.RED.value,
                message="Hardware error / hard lockup / watchdog reset found in kernel log.",
            )
        )
    if kernel_scan["soft_lockup_count"] > 0:
        findings.append(
            HardwareFinding(
                code="cpu.hardware_error_detected",
                severity=BaselineSeverity.YELLOW.value,
                message=f"{kernel_scan['soft_lockup_count']} soft-lockup event(s) found in kernel log.",
            )
        )

    checks_run.append("thermal_zone_read")
    zones = read_thermal_zone_temperatures(sysfs_root=sysfs_root)
    max_temp = max((z["temperature_c"] for z in zones if z["temperature_c"] is not None), default=None)
    if not zones:
        checks_skipped.append("thermal_zones")
    else:
        metrics.append(HardwareMetric(name="max_thermal_zone_temperature_c", value=max_temp, unit="C"))

    throttling = detect_thermal_throttling(dmesg_text)
    if throttling:
        findings.append(
            HardwareFinding(code="cpu.throttling_detected", severity=BaselineSeverity.YELLOW.value, message="Thermal throttling reported in kernel log.")
        )
    if max_temp is not None and max_temp >= _THERMAL_WARNING_TEMP_C:
        findings.append(
            HardwareFinding(
                code="cpu.thermal_warning",
                severity=BaselineSeverity.YELLOW.value,
                message=f"A thermal zone reports {max_temp:.1f}\u00b0C (>= {_THERMAL_WARNING_TEMP_C}\u00b0C warning threshold).",
            )
        )

    probe_result: dict[str, Any] | None = None
    if skip_quick_probe:
        checks_skipped.append("quick_cpu_probe")
    else:
        checks_run.append("quick_cpu_probe")
        probe_result = run_quick_cpu_probe(
            max_temp_c=max_temp, worker=probe_worker, clock=probe_clock, force_result=force_probe_result
        )
        metrics.append(HardwareMetric(name="quick_probe_status", value=probe_result["status"]))
        metrics.append(HardwareMetric(name="quick_probe_duration_ms", value=probe_result["duration_ms"], unit="ms"))
        if probe_result["status"] == "checksum_mismatch":
            findings.append(
                HardwareFinding(code="cpu.quick_probe_failed", severity=BaselineSeverity.RED.value, message="Quick CPU probe checksum mismatch.")
            )
        elif probe_result["status"] == "timeout":
            findings.append(
                HardwareFinding(code="cpu.quick_probe_timeout", severity=BaselineSeverity.YELLOW.value, message="Quick CPU probe exceeded its timeout.")
            )

    has_red = any(f.severity == BaselineSeverity.RED.value for f in findings)
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)

    extended_test = ExtendedTestRecommendation()
    if has_red:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="cpu_stress", estimated_duration="1_to_several_hours")
        findings.append(
            HardwareFinding(
                code="cpu.extended_stress_test_recommended",
                severity=BaselineSeverity.YELLOW.value,
                message="A supervised, multi-hour CPU stability test is recommended before trusting this CPU under sustained load.",
            )
        )
        recommendations.append("Avoid sustained full-load operations (OS install/restore) until reviewed.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="cpu_stress", estimated_duration="1_to_several_hours")
        recommendations.append("Consider a supervised CPU stability test if instability is observed.")
    else:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.CPU.value,
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
    )


def build_cpu_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": CPU_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.cpu_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "installs_tools": False,
        "triggers_microcode_update": False,
        "triggers_bios_update": False,
        "quick_probe_default_timeout_s": _QUICK_PROBE_DEFAULT_TIMEOUT_S,
    }


__all__ = [
    "CPU_BASELINE_DIAGNOSTICS_VERSION",
    "scan_kernel_cpu_errors",
    "read_thermal_zone_temperatures",
    "detect_thermal_throttling",
    "run_quick_cpu_probe",
    "build_cpu_baseline_result",
    "build_cpu_baseline_diagnostics",
]
