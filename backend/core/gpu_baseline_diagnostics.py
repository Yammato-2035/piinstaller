"""
GPU baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 5.

Reuses ``core.gpu_detection.build_gpu_report`` (PCI GPU detection, driver-in-
use, DRM card/connector presence, disabling kernel cmdline params) as its
sole source of GPU inventory/state — this module never re-detects GPUs
itself. It only adds:

1. render node presence check (``/dev/dri/renderD*`` — distinct from the DRM
   *card*/control node ``gpu_detection`` already checks)
2. kernel/firmware GPU error scan (``dmesg``)
3. optional, safe display-capability probes (``glxinfo``/``eglinfo``/
   ``vulkaninfo``) — read-only queries, never a render/stress benchmark

Distinguishes critical kernel-reported GPU errors (red — likely a real
hardware/driver-stability problem) from driver/firmware *absence* (yellow —
commonly just a missing optional package, not a hardware fault). Never
installs a GPU driver or firmware package, never modifies the kernel
cmdline or modprobe blacklist.
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
from core.gpu_detection import build_gpu_report
from core.hardware_contracts import HardwareDevice

GPU_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_OPTIONAL_PROBE_TOOLS = ("glxinfo", "eglinfo", "vulkaninfo")


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


def check_render_node_presence(*, dev_root: Path | None = None) -> list[str]:
    """List present ``/dev/dri/renderD*`` nodes (never the card/control node —
    that presence is already covered by ``gpu_detection.collect_drm_cards``)."""
    root = dev_root or Path("/")
    base = root / "dev" / "dri"
    if not base.exists():
        return []
    try:
        return sorted(p.name for p in base.glob("renderD*"))
    except OSError:
        return []


def scan_kernel_gpu_errors(dmesg_text: str | None = None, *, runner: Runner = None) -> dict[str, Any]:
    """Scan kernel log text for GPU firmware-load failures and GPU
    hang/reset/fence-timeout/Xid errors. Read-only; a missing ``dmesg``
    never crashes this."""
    missing_tools: list[str] = []
    text = dmesg_text
    if text is None:
        text, present = _run_tool(["dmesg"], runner=runner)
        if not present:
            missing_tools.append("dmesg")
    text = text or ""

    firmware_missing = len(re.findall(r"failed to load firmware|firmware.*(?:not found|failed)", text, re.IGNORECASE))
    gpu_hang = len(re.findall(r"GPU HANG|amdgpu.*ring.*timeout|i915.*GPU HANG|nouveau.*fault|Xid", text, re.IGNORECASE))
    fence_timeout = len(re.findall(r"fence.*timeout|drm.*reset", text, re.IGNORECASE))

    return {
        "firmware_load_failed_count": firmware_missing,
        "gpu_hang_or_reset_count": gpu_hang,
        "fence_timeout_count": fence_timeout,
        "missing_tools": missing_tools,
    }


def run_optional_display_probe(tool: str, *, runner: Runner = None) -> dict[str, Any]:
    """Run one optional, read-only display-capability probe. A missing tool
    is never treated as an error — it is simply unavailable."""
    argv = {"glxinfo": ["glxinfo", "-B"], "eglinfo": ["eglinfo"], "vulkaninfo": ["vulkaninfo", "--summary"]}.get(tool, [tool])
    output, present = _run_tool(argv, runner=runner, timeout=5)
    return {"tool": tool, "available": present, "output_length": len(output)}


def build_gpu_baseline_result(
    *,
    pci_devices: list[HardwareDevice],
    cmdline_raw: str = "",
    sysfs_root: Path | None = None,
    dev_root: Path | None = None,
    dmesg_text: str | None = None,
    runner: Runner = None,
    run_optional_probes: bool = True,
    probe_tools: tuple[str, ...] = _OPTIONAL_PROBE_TOOLS,
) -> HardwareSubsystemResult:
    started_at = _utc_now()
    t0 = time.monotonic()

    checks_run: list[str] = ["gpu_detection"]
    checks_skipped: list[str] = []
    findings: list[HardwareFinding] = []
    metrics: list[HardwareMetric] = []
    recommendations: list[str] = []

    reports = build_gpu_report(pci_devices=pci_devices, cmdline_raw=cmdline_raw, sysfs_root=sysfs_root)
    metrics.append(HardwareMetric(name="gpu_device_count", value=len(reports)))

    if not reports:
        completed_at = _utc_now()
        return HardwareSubsystemResult(
            subsystem=BaselineSubsystem.GPU.value,
            status=BaselineStatus.NOT_TESTED.value,
            severity=BaselineSeverity.GRAY.value,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=int((time.monotonic() - t0) * 1000),
            checks_run=tuple(checks_run),
            checks_skipped=("gpu_health_checks:no_gpu_pci_device_found",),
            metrics=tuple(metrics),
            findings=(HardwareFinding(code="gpu.no_device_detected", severity=BaselineSeverity.GRAY.value, message="No GPU PCI device detected (headless system?)."),),
        )

    checks_run.append("render_node_presence")
    render_nodes = check_render_node_presence(dev_root=dev_root)
    metrics.append(HardwareMetric(name="render_node_count", value=len(render_nodes)))

    checks_run.append("kernel_error_scan")
    kernel_scan = scan_kernel_gpu_errors(dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    for key in ("firmware_load_failed_count", "gpu_hang_or_reset_count", "fence_timeout_count"):
        metrics.append(HardwareMetric(name=key, value=kernel_scan[key]))

    has_kernel_error = kernel_scan["gpu_hang_or_reset_count"] > 0 or kernel_scan["fence_timeout_count"] > 0
    if has_kernel_error:
        findings.append(
            HardwareFinding(
                code="gpu.kernel_error_detected",
                severity=BaselineSeverity.RED.value,
                message="GPU hang/reset/fence-timeout reported in kernel log.",
            )
        )
    if kernel_scan["firmware_load_failed_count"] > 0:
        findings.append(
            HardwareFinding(
                code="gpu.firmware_missing",
                severity=BaselineSeverity.YELLOW.value,
                message="GPU firmware failed to load according to the kernel log.",
            )
        )

    hybrid = len(reports) > 1
    if hybrid:
        metrics.append(HardwareMetric(name="hybrid_graphics", value=True))

    any_ready = False
    for entry in reports:
        device_id = entry["device_id"]
        gpu_status = entry["gpu_status"]
        if gpu_status == "ready":
            any_ready = True
            continue
        if gpu_status == "disabled_by_cmdline":
            findings.append(
                HardwareFinding(
                    code="gpu.disabled_by_cmdline",
                    severity=BaselineSeverity.YELLOW.value,
                    message=f"GPU {device_id} disabled via kernel cmdline: {', '.join(entry['disabling_cmdline_params'])}.",
                )
            )
        elif gpu_status == "driver_missing":
            findings.append(
                HardwareFinding(
                    code="gpu.driver_missing",
                    severity=BaselineSeverity.YELLOW.value,
                    message=f"No kernel driver in use for GPU {device_id}.",
                )
            )
        elif gpu_status == "limited":
            if not entry["drm_card_present"]:
                findings.append(
                    HardwareFinding(
                        code="gpu.drm_device_missing",
                        severity=BaselineSeverity.YELLOW.value,
                        message=f"No DRM card device created for GPU {device_id}.",
                    )
                )
            else:
                findings.append(
                    HardwareFinding(
                        code="gpu.no_active_connector",
                        severity=BaselineSeverity.YELLOW.value,
                        message=f"GPU {device_id} has a DRM card but no active display connector.",
                    )
                )

    if reports and not render_nodes:
        findings.append(
            HardwareFinding(
                code="gpu.render_node_missing",
                severity=BaselineSeverity.YELLOW.value,
                message="No /dev/dri/renderD* render node present; GPU-accelerated render tests are not possible.",
            )
        )

    probe_results: list[dict[str, Any]] = []
    if run_optional_probes:
        checks_run.append("optional_display_probes")
        for tool in probe_tools:
            probe = run_optional_display_probe(tool, runner=runner)
            probe_results.append(probe)
            if not probe["available"]:
                checks_skipped.append(f"optional_probe:{tool}")
            metrics.append(HardwareMetric(name=f"probe_{tool}_available", value=probe["available"]))
    else:
        checks_skipped.append("optional_display_probes")

    has_red = any(f.severity == BaselineSeverity.RED.value for f in findings)
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)

    extended_test = ExtendedTestRecommendation()
    if has_red:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="gpu_render_stress", estimated_duration="30_to_60_minutes")
        findings.append(
            HardwareFinding(
                code="gpu.extended_render_test_recommended",
                severity=BaselineSeverity.YELLOW.value,
                message="A supervised GPU render-stress test is recommended before relying on GUI mode for extended sessions.",
            )
        )
        recommendations.append("Prefer safe TUI-only mode until the GPU kernel error is reviewed.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        recommendations.append("GUI mode may be degraded or unavailable; safe TUI-only fallback recommended.")
    elif any_ready:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value
    else:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.GPU.value,
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


def build_gpu_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": GPU_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.gpu_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "installs_driver_or_firmware": False,
        "modifies_kernel_cmdline": False,
        "modifies_modprobe_blacklist": False,
        "optional_probe_tools": list(_OPTIONAL_PROBE_TOOLS),
    }


__all__ = [
    "GPU_BASELINE_DIAGNOSTICS_VERSION",
    "check_render_node_presence",
    "scan_kernel_gpu_errors",
    "run_optional_display_probe",
    "build_gpu_baseline_result",
    "build_gpu_baseline_diagnostics",
]
