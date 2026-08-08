"""
Kernel-log event classification helpers for hardware baseline heuristics.

PI-RS-ASUS-ROOTCAUSE-006B — distinguish informational subsystem messages from
real hardware-fault signals (MCE, GPU reset) without weakening real errors.
"""

from __future__ import annotations

import re
from typing import Any

KERNEL_EVENT_CLASSIFICATION_VERSION = 1

# Capability / subsystem bring-up — must NOT count as a machine-check event.
_MCE_INFORMATIONAL_RES = (
    re.compile(r"MCE:\s*In-kernel MCE decoding enabled\.?", re.IGNORECASE),
    re.compile(r"MCE:\s*.*(initialized|initialised|available|polling enabled|subsystem)", re.IGNORECASE),
    re.compile(r"mce:\s*Using (?:generic|default) MCA", re.IGNORECASE),
)

# Real / likely machine-check fault signals.
_MCE_UNCORRECTED_RES = (
    re.compile(r"mce:.*\[Hardware Error\]", re.IGNORECASE),
    re.compile(r"Machine check events logged", re.IGNORECASE),
    re.compile(r"Machine Check Exception", re.IGNORECASE),
    re.compile(r"mce:.*\buncorrected\b", re.IGNORECASE),
    re.compile(r"processor context corrupt", re.IGNORECASE),
    re.compile(r"CPU\d+:\s*Machine Check", re.IGNORECASE),
)

_MCE_CORRECTED_RES = (
    re.compile(r"mce:.*\bcorrected\b", re.IGNORECASE),
    re.compile(r"Corrected (?:hardware )?error", re.IGNORECASE),
)

# Expected single-shot GPU init chatter seen on ASUS AMD bring-up.
# Keep this narrow — generic "GPU reset" lines must still be reviewed via hang/fail patterns.
_GPU_EXPECTED_RESET_RES = (
    re.compile(r"\bMODE2 reset\b", re.IGNORECASE),
)

# Real GPU fault / failed reset signals (keep strict).
_GPU_HANG_RES = (
    re.compile(r"GPU HANG", re.IGNORECASE),
    re.compile(r"amdgpu.*ring.*timeout", re.IGNORECASE),
    re.compile(r"i915.*GPU HANG", re.IGNORECASE),
    re.compile(r"nouveau.*fault", re.IGNORECASE),
    re.compile(r"\bXid\b"),
)

_GPU_BAD_RESET_RES = (
    re.compile(r"fence.*timeout", re.IGNORECASE),
    re.compile(r"reset(?:ting)?.*timeout", re.IGNORECASE),
    re.compile(r"reset failed", re.IGNORECASE),
    re.compile(r"failed to reset", re.IGNORECASE),
    re.compile(r"controller reset.*(?:I/O|io) error", re.IGNORECASE),
    re.compile(r"device disappeared", re.IGNORECASE),
)


def _lines(text: str) -> list[str]:
    return [ln for ln in (text or "").splitlines() if ln.strip()]


def classify_mce_dmesg(dmesg_text: str) -> dict[str, Any]:
    """Classify MCE-related kernel lines into informational vs real events."""
    informational: list[str] = []
    corrected: list[str] = []
    uncorrected: list[str] = []
    for ln in _lines(dmesg_text):
        if not re.search(r"\bMCE\b|mce:|Machine Check", ln, re.IGNORECASE):
            continue
        if any(p.search(ln) for p in _MCE_INFORMATIONAL_RES):
            informational.append(ln)
            continue
        if any(p.search(ln) for p in _MCE_UNCORRECTED_RES):
            uncorrected.append(ln)
            continue
        if any(p.search(ln) for p in _MCE_CORRECTED_RES):
            corrected.append(ln)
            continue
        # Unknown MCE-ish line → review, do not auto-red.
        informational.append(ln)

    return {
        "informational_lines": informational,
        "corrected_lines": corrected,
        "uncorrected_lines": uncorrected,
        "informational_count": len(informational),
        "corrected_count": len(corrected),
        "uncorrected_count": len(uncorrected),
        # Backward-compatible "real event" counters used by baseline scanners.
        "mce_event_count": len(corrected) + len(uncorrected),
        "mce_uncorrected_count": len(uncorrected),
        "mce_corrected_count": len(corrected),
    }


def classify_gpu_reset_dmesg(dmesg_text: str) -> dict[str, Any]:
    """Classify GPU hang/reset lines; MODE2/init resets are not critical alone."""
    expected: list[str] = []
    hangs: list[str] = []
    bad_resets: list[str] = []
    for ln in _lines(dmesg_text):
        if any(p.search(ln) for p in _GPU_HANG_RES):
            hangs.append(ln)
            continue
        if any(p.search(ln) for p in _GPU_BAD_RESET_RES):
            bad_resets.append(ln)
            continue
        if any(p.search(ln) for p in _GPU_EXPECTED_RESET_RES):
            # Only treat as expected when no failure marker on the same line.
            if re.search(r"fail|timeout|error|I/O", ln, re.IGNORECASE):
                bad_resets.append(ln)
            else:
                expected.append(ln)

    return {
        "expected_reset_lines": expected,
        "hang_lines": hangs,
        "bad_reset_lines": bad_resets,
        "expected_reset_count": len(expected),
        "gpu_hang_or_reset_count": len(hangs),
        "fence_timeout_count": len(bad_resets),
        "critical_count": len(hangs) + len(bad_resets),
    }


def parse_modprobe_blacklist_modules(cmdline_raw: str) -> set[str]:
    """Return module names listed in modprobe.blacklist=… cmdline tokens."""
    out: set[str] = set()
    for tok in (cmdline_raw or "").split():
        if not tok.startswith("modprobe.blacklist="):
            continue
        payload = tok.split("=", 1)[1]
        for name in payload.split(","):
            name = name.strip()
            if name:
                out.add(name)
    return out


_VENDOR_BLACKLIST_MODULES = {
    "nvidia": ("nvidia", "nvidia_drm", "nvidia_modeset", "nvidia_uvm", "nouveau"),
    "amd": ("amdgpu", "radeon"),
    "intel": ("i915", "xe"),
}


def detect_intentional_driver_blacklist(cmdline_raw: str, vendor: str) -> list[str]:
    """Return blacklist evidence tokens when vendor drivers are intentionally suppressed."""
    listed = parse_modprobe_blacklist_modules(cmdline_raw)
    wanted = _VENDOR_BLACKLIST_MODULES.get(vendor, ())
    hits = [m for m in wanted if m in listed]
    return [f"modprobe.blacklist={m}" for m in hits]


__all__ = [
    "KERNEL_EVENT_CLASSIFICATION_VERSION",
    "classify_mce_dmesg",
    "classify_gpu_reset_dmesg",
    "parse_modprobe_blacklist_modules",
    "detect_intentional_driver_blacklist",
]
