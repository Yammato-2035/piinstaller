"""
Memory (RAM) baseline diagnostics — early, read-only risk check.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 3.

Deliberate parallel path (see docs/evidence/rescue/hardware-baseline-002/
HARDWARE_BASELINE_IST_AUDIT.md): ``core.hardware_discovery`` remains the
display-oriented inventory facade for the product app; this module adds
baseline *health* checks (EDAC/MCE/OOM, bounded quick probe) and does not
replace or duplicate that discovery facade.

Four independent, additive checks, all read-only except the bounded quick
memory probe (which only ever allocates and immediately releases a small,
capped Python buffer — never a system-level memtest):

1. inventory (``/proc/meminfo`` + optional ``dmidecode`` RAM modules)
2. kernel/hardware error scan (EDAC/MCE/OOM via ``dmesg``)
3. plausibility check (physical vs. kernel-usable memory)
4. bounded quick memory probe (never a full Memtest — see
   ``run_quick_memory_probe``)

Never installs ``memtester``/``stress-ng``/``rasdaemon``/``dmidecode``; when a
tool is missing the affected check is ``test_unavailable``/``checks_skipped``,
never a fabricated "passed_full_memtest".
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
from core.kernel_event_classification import classify_mce_dmesg

MEMORY_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None

_QUICK_PROBE_MAX_BYTES = 128 * 1024 * 1024  # 128 MiB hard ceiling
_QUICK_PROBE_PCT_OF_AVAILABLE = 0.02  # 2 % of MemAvailable
_QUICK_PROBE_MIN_RESERVE_KB = 256 * 1024  # keep at least 256 MiB free after probe
_QUICK_PROBE_SKIP_BELOW_AVAILABLE_KB = 512 * 1024  # skip probe below 512 MiB available
_QUICK_PROBE_TIMEOUT_S = 3.0
_CAPACITY_MISMATCH_RATIO = 0.85  # kernel-usable < 85% of DMI-reported physical is suspicious
_EXTREMELY_LOW_AVAILABLE_KB = 128 * 1024  # < 128 MiB available is a red flag


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 10) -> tuple[str, bool]:
    """Run a read-only diagnostic tool with a hard timeout. Never raises;
    returns (stdout, tool_present)."""
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


def parse_meminfo(text: str) -> dict[str, int | None]:
    """Parse ``/proc/meminfo``-style text. Values are kB (as reported by the kernel)."""
    out: dict[str, int | None] = {
        "mem_total_kb": None,
        "mem_available_kb": None,
        "mem_free_kb": None,
        "swap_total_kb": None,
        "swap_free_kb": None,
        "huge_pages_total": None,
        "huge_pages_free": None,
    }
    field_map = {
        "MemTotal": "mem_total_kb",
        "MemAvailable": "mem_available_kb",
        "MemFree": "mem_free_kb",
        "SwapTotal": "swap_total_kb",
        "SwapFree": "swap_free_kb",
        "HugePages_Total": "huge_pages_total",
        "HugePages_Free": "huge_pages_free",
    }
    for line in (text or "").splitlines():
        m = re.match(r"^(\w+):\s+(\d+)", line)
        if not m:
            continue
        key, value = m.group(1), int(m.group(2))
        if key in field_map:
            out[field_map[key]] = value
    return out


def parse_dmi_memory_devices(dmidecode_text: str) -> list[dict[str, Any]]:
    """Parse ``dmidecode -t memory`` "Memory Device" blocks (best-effort,
    tolerant of missing fields — DMI data quality varies a lot by vendor)."""
    if not dmidecode_text:
        return []
    modules: list[dict[str, Any]] = []
    blocks = re.split(r"\n(?=Memory Device\b)", dmidecode_text)
    for block in blocks:
        if "Memory Device" not in block:
            continue
        size_m = re.search(r"^\s*Size:\s*(.+)$", block, re.MULTILINE)
        size_raw = size_m.group(1).strip() if size_m else None
        if size_raw and "no module" in size_raw.lower():
            continue
        speed_m = re.search(r"^\s*Speed:\s*(.+)$", block, re.MULTILINE)
        type_m = re.search(r"^\s*Type:\s*(.+)$", block, re.MULTILINE)
        manufacturer_m = re.search(r"^\s*Manufacturer:\s*(.+)$", block, re.MULTILINE)
        locator_m = re.search(r"^\s*Locator:\s*(.+)$", block, re.MULTILINE)
        if size_raw is None and type_m is None:
            continue
        modules.append(
            {
                "size": size_raw,
                "speed": speed_m.group(1).strip() if speed_m else None,
                "type": type_m.group(1).strip() if type_m else None,
                "manufacturer": manufacturer_m.group(1).strip() if manufacturer_m else None,
                "locator": locator_m.group(1).strip() if locator_m else None,
            }
        )
    return modules


def detect_ecc_support(dmidecode_text: str) -> bool | None:
    """Return True/False only when ECC state is unambiguously reported by
    DMI; otherwise None (never guess — spec: only claim ECC when belastbar
    feststellbar)."""
    if not dmidecode_text:
        return None
    m = re.search(r"^\s*Error Correction Type:\s*(.+)$", dmidecode_text, re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip().lower()
    if value in ("none", "unknown"):
        return False if value == "none" else None
    return True


def collect_memory_inventory(
    *, meminfo_text: str | None = None, dmidecode_text: str | None = None, runner: Runner = None
) -> dict[str, Any]:
    """Read-only inventory. If ``meminfo_text``/``dmidecode_text`` are not
    injected, this reads the real system (``/proc/meminfo``) and calls the
    real ``dmidecode`` tool (missing tool -> empty module list, not an
    error)."""
    if meminfo_text is None:
        try:
            with open("/proc/meminfo", encoding="utf-8", errors="ignore") as fh:
                meminfo_text = fh.read()
        except OSError:
            meminfo_text = ""
    parsed = parse_meminfo(meminfo_text or "")

    dmi_text = dmidecode_text
    dmidecode_present = dmi_text is not None
    if dmi_text is None:
        dmi_text, dmidecode_present = _run_tool(["dmidecode", "-t", "memory"], runner=runner)

    modules = parse_dmi_memory_devices(dmi_text or "")
    ecc = detect_ecc_support(dmi_text or "")
    return {
        **parsed,
        "ram_modules": modules,
        "ecc_supported": ecc,
        "dmidecode_available": dmidecode_present,
    }


def scan_kernel_memory_errors(dmesg_text: str | None = None, *, runner: Runner = None) -> dict[str, Any]:
    """Scan kernel log text for EDAC/MCE/OOM signals. Read-only; ``dmesg``
    permission errors or a missing tool never crash this — they yield an
    empty, non-fabricated result plus a ``missing_tools`` entry."""
    missing_tools: list[str] = []
    text = dmesg_text
    if text is None:
        text, present = _run_tool(["dmesg"], runner=runner)
        if not present:
            missing_tools.append("dmesg")
    text = text or ""

    edac_corrected = len(re.findall(r"EDAC.*correctable error", text, re.IGNORECASE))
    edac_uncorrected = len(re.findall(r"EDAC.*uncorrectable error", text, re.IGNORECASE))
    mce = classify_mce_dmesg(text)
    # Real machine-check events only — "MCE decoding enabled" is informational.
    mce_count = int(mce["mce_event_count"])
    oom_count = len(re.findall(r"Out of memory:|oom-kill", text, re.IGNORECASE))

    return {
        "edac_corrected_count": edac_corrected,
        "edac_uncorrected_count": edac_uncorrected,
        "mce_count": mce_count,
        "mce_informational_count": int(mce["informational_count"]),
        "mce_corrected_count": int(mce["mce_corrected_count"]),
        "mce_uncorrected_count": int(mce["mce_uncorrected_count"]),
        "mce_informational_lines": list(mce["informational_lines"]),
        "mce_corrected_lines": list(mce["corrected_lines"]),
        "mce_uncorrected_lines": list(mce["uncorrected_lines"]),
        "oom_count": oom_count,
        "missing_tools": missing_tools,
    }


def check_memory_plausibility(inventory: dict[str, Any]) -> list[HardwareFinding]:
    """Compare kernel-usable memory against DMI-reported physical capacity
    and flag extremely low available memory. Never claims exact byte
    equality is required (BIOS/UMA/reserved regions legitimately differ)."""
    findings: list[HardwareFinding] = []
    mem_total_kb = inventory.get("mem_total_kb")
    mem_available_kb = inventory.get("mem_available_kb")

    dmi_total_kb = 0
    any_dmi_size = False
    for module in inventory.get("ram_modules") or []:
        size = module.get("size") or ""
        m = re.match(r"^\s*(\d+)\s*(MB|GB)\s*$", size, re.IGNORECASE)
        if m:
            any_dmi_size = True
            value, unit = int(m.group(1)), m.group(2).upper()
            dmi_total_kb += value * (1024 * 1024 if unit == "GB" else 1024)

    if any_dmi_size and mem_total_kb and dmi_total_kb > 0:
        ratio = mem_total_kb / dmi_total_kb
        if ratio < _CAPACITY_MISMATCH_RATIO:
            findings.append(
                HardwareFinding(
                    code="memory.capacity_mismatch",
                    severity=BaselineSeverity.YELLOW.value,
                    message=(
                        f"Kernel-usable memory ({mem_total_kb} kB) is notably lower than DMI-reported "
                        f"physical capacity ({dmi_total_kb} kB)."
                    ),
                )
            )

    if mem_available_kb is not None and mem_available_kb < _EXTREMELY_LOW_AVAILABLE_KB:
        findings.append(
            HardwareFinding(
                code="memory.extremely_low_available",
                severity=BaselineSeverity.YELLOW.value,
                message=f"MemAvailable is only {mem_available_kb} kB.",
            )
        )
    return findings


def run_quick_memory_probe(
    mem_available_kb: int | None,
    *,
    allocator: Callable[[int], Any] | None = None,
    clock: Callable[[], float] | None = None,
    timeout_s: float = _QUICK_PROBE_TIMEOUT_S,
    force_result: str | None = None,
) -> dict[str, Any]:
    """Bounded, in-process quick memory probe.

    Never a full Memtest: allocates at most ``min(128 MiB, 2% of
    MemAvailable)``, writes a small deterministic pattern, verifies it, then
    releases the buffer immediately. Skips entirely when available memory
    is too low to leave a safe reserve. No root required (pure Python
    ``bytearray``, no ``mmap``/``mlock``).

    ``force_result`` is test-only ("failed"/"timeout") to deterministically
    exercise error paths without depending on real memory corruption.
    """
    if mem_available_kb is None or mem_available_kb < _QUICK_PROBE_SKIP_BELOW_AVAILABLE_KB:
        return {"status": "skipped_low_available", "tested_bytes": 0}

    budget_kb = min(_QUICK_PROBE_MAX_BYTES // 1024, int(mem_available_kb * _QUICK_PROBE_PCT_OF_AVAILABLE))
    if budget_kb <= 0 or (mem_available_kb - budget_kb) < _QUICK_PROBE_MIN_RESERVE_KB:
        return {"status": "skipped_low_available", "tested_bytes": 0}

    tested_bytes = budget_kb * 1024
    _clock = clock or time.monotonic
    start = _clock()

    if force_result == "timeout":
        return {"status": "timeout", "tested_bytes": tested_bytes}
    if force_result == "failed":
        return {"status": "failed", "tested_bytes": tested_bytes}

    try:
        alloc = allocator or (lambda n: bytearray(n))
        buf = alloc(tested_bytes)
        pattern = bytes((i % 256 for i in range(256)))
        for i in range(0, tested_bytes, 256):
            end = min(i + 256, tested_bytes)
            buf[i:end] = pattern[: end - i]
        if _clock() - start > timeout_s:
            del buf
            return {"status": "timeout", "tested_bytes": tested_bytes}
        ok = True
        for i in range(0, tested_bytes, 256):
            end = min(i + 256, tested_bytes)
            if bytes(buf[i:end]) != pattern[: end - i]:
                ok = False
                break
        del buf
        return {"status": "success" if ok else "failed", "tested_bytes": tested_bytes}
    except MemoryError:
        return {"status": "failed", "tested_bytes": tested_bytes}


def build_memory_baseline_result(
    *,
    meminfo_text: str | None = None,
    dmidecode_text: str | None = None,
    dmesg_text: str | None = None,
    runner: Runner = None,
    skip_quick_probe: bool = False,
    probe_allocator: Callable[[int], Any] | None = None,
    probe_clock: Callable[[], float] | None = None,
    force_probe_result: str | None = None,
) -> HardwareSubsystemResult:
    started_at = _utc_now()
    t0 = time.monotonic()

    checks_run: list[str] = ["meminfo_inventory"]
    checks_skipped: list[str] = []
    findings: list[HardwareFinding] = []
    metrics: list[HardwareMetric] = []
    recommendations: list[str] = []

    inventory = collect_memory_inventory(meminfo_text=meminfo_text, dmidecode_text=dmidecode_text, runner=runner)
    if not inventory.get("dmidecode_available"):
        checks_skipped.append("dmidecode")
    else:
        checks_run.append("dmi_ram_module_inventory")

    for key in ("mem_total_kb", "mem_available_kb", "swap_total_kb", "swap_free_kb"):
        if inventory.get(key) is not None:
            metrics.append(HardwareMetric(name=key, value=inventory[key], unit="kB", source="/proc/meminfo"))
    metrics.append(HardwareMetric(name="ram_module_count", value=len(inventory.get("ram_modules") or [])))
    if inventory.get("ecc_supported") is not None:
        metrics.append(HardwareMetric(name="ecc_supported", value=inventory["ecc_supported"]))

    checks_run.append("kernel_error_scan")
    kernel_scan = scan_kernel_memory_errors(dmesg_text, runner=runner)
    checks_skipped.extend(kernel_scan.get("missing_tools") or [])
    metrics.append(HardwareMetric(name="edac_corrected_count", value=kernel_scan["edac_corrected_count"]))
    metrics.append(HardwareMetric(name="edac_uncorrected_count", value=kernel_scan["edac_uncorrected_count"]))
    metrics.append(HardwareMetric(name="mce_count", value=kernel_scan["mce_count"]))
    metrics.append(HardwareMetric(name="mce_informational_count", value=kernel_scan.get("mce_informational_count", 0)))
    metrics.append(HardwareMetric(name="oom_count", value=kernel_scan["oom_count"]))

    if kernel_scan["edac_uncorrected_count"] > 0:
        findings.append(
            HardwareFinding(
                code="memory.kernel_uncorrected_error",
                severity=BaselineSeverity.RED.value,
                message=f"{kernel_scan['edac_uncorrected_count']} uncorrected EDAC memory error(s) found in kernel log.",
                category="critical",
                action_blocking=True,
                confidence=0.95,
            )
        )
    if kernel_scan.get("mce_informational_count", 0) > 0 and kernel_scan["mce_count"] == 0:
        findings.append(
            HardwareFinding(
                code="memory.mce_decoder_enabled",
                severity=BaselineSeverity.GRAY.value,
                message="MCE decoder/capability messages present; no real machine-check event classified.",
                evidence=tuple(kernel_scan.get("mce_informational_lines") or ())[:5],
                category="informational",
                action_blocking=False,
                confidence=0.99,
            )
        )
    if kernel_scan.get("mce_uncorrected_count", 0) > 0:
        findings.append(
            HardwareFinding(
                code="memory.kernel_uncorrected_error",
                severity=BaselineSeverity.RED.value,
                message=f"{kernel_scan['mce_uncorrected_count']} uncorrected machine-check event(s) found in kernel log.",
                evidence=tuple(kernel_scan.get("mce_uncorrected_lines") or ())[:5],
                category="critical",
                action_blocking=True,
                confidence=0.95,
            )
        )
    elif kernel_scan.get("mce_corrected_count", 0) > 0:
        findings.append(
            HardwareFinding(
                code="memory.kernel_corrected_mce",
                severity=BaselineSeverity.YELLOW.value,
                message=f"{kernel_scan['mce_corrected_count']} corrected machine-check event(s) found in kernel log.",
                evidence=tuple(kernel_scan.get("mce_corrected_lines") or ())[:5],
                category="warning",
                action_blocking=False,
                confidence=0.9,
            )
        )
    if kernel_scan["edac_corrected_count"] > 0:
        findings.append(
            HardwareFinding(
                code="memory.kernel_corrected_error",
                severity=BaselineSeverity.YELLOW.value,
                message=f"{kernel_scan['edac_corrected_count']} corrected EDAC memory error(s) found in kernel log.",
            )
        )
    if kernel_scan["oom_count"] > 0:
        findings.append(
            HardwareFinding(
                code="memory.oom_history_detected",
                severity=BaselineSeverity.YELLOW.value,
                message=f"{kernel_scan['oom_count']} out-of-memory event(s) found in kernel log.",
            )
        )

    checks_run.append("plausibility_check")
    findings.extend(check_memory_plausibility(inventory))

    probe_result: dict[str, Any] | None = None
    if skip_quick_probe:
        checks_skipped.append("quick_memory_probe")
    else:
        checks_run.append("quick_memory_probe")
        probe_result = run_quick_memory_probe(
            inventory.get("mem_available_kb"),
            allocator=probe_allocator,
            clock=probe_clock,
            force_result=force_probe_result,
        )
        metrics.append(HardwareMetric(name="quick_probe_status", value=probe_result["status"]))
        metrics.append(HardwareMetric(name="quick_probe_tested_bytes", value=probe_result["tested_bytes"], unit="bytes"))
        if probe_result["status"] == "skipped_low_available":
            findings.append(
                HardwareFinding(
                    code="memory.quick_probe_skipped_low_available",
                    severity=BaselineSeverity.GRAY.value,
                    message="Quick memory probe skipped: not enough MemAvailable to leave a safe reserve.",
                )
            )
        elif probe_result["status"] in ("failed", "timeout"):
            findings.append(
                HardwareFinding(
                    code="memory.quick_probe_failed",
                    severity=BaselineSeverity.RED.value,
                    message=f"Quick memory probe result: {probe_result['status']}.",
                )
            )

    has_uncorrected_or_probe_failed = any(
        f.code in ("memory.kernel_uncorrected_error", "memory.quick_probe_failed") for f in findings
    )
    has_yellow = any(f.severity == BaselineSeverity.YELLOW.value for f in findings)

    extended_test = ExtendedTestRecommendation()
    if has_uncorrected_or_probe_failed:
        status = BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.RED.value
        extended_test = ExtendedTestRecommendation(
            recommended=True,
            required=True,
            test_type="memtest86plus",
            estimated_duration="several_hours",
        )
        findings.append(
            HardwareFinding(
                code="memory.extended_memtest_required",
                severity=BaselineSeverity.RED.value,
                message="A full Memtest86+/UEFI memory diagnostic run is required before this memory can be trusted for restore or installation.",
            )
        )
        recommendations.append("Run a full Memtest86+ or vendor UEFI memory diagnostic before restore/installation.")
    elif has_yellow:
        status = BaselineStatus.REVIEW_REQUIRED.value
        severity = BaselineSeverity.YELLOW.value
        extended_test = ExtendedTestRecommendation(recommended=True, test_type="memtest86plus", estimated_duration="several_hours")
        recommendations.append("Consider a full memory test if symptoms (crashes, corruption) are observed.")
    else:
        status = BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        severity = BaselineSeverity.GREEN.value

    completed_at = _utc_now()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return HardwareSubsystemResult(
        subsystem=BaselineSubsystem.MEMORY.value,
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


def build_memory_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": MEMORY_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.memory_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "installs_tools": False,
        "quick_probe_max_bytes": _QUICK_PROBE_MAX_BYTES,
        "quick_probe_pct_of_available": _QUICK_PROBE_PCT_OF_AVAILABLE,
    }


__all__ = [
    "MEMORY_BASELINE_DIAGNOSTICS_VERSION",
    "parse_meminfo",
    "parse_dmi_memory_devices",
    "detect_ecc_support",
    "collect_memory_inventory",
    "scan_kernel_memory_errors",
    "check_memory_plausibility",
    "run_quick_memory_probe",
    "build_memory_baseline_result",
    "build_memory_baseline_diagnostics",
]
