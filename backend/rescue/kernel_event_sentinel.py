"""
Kernel event sentinel — bounded, redacted kernel/log excerpts as structured events.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 4.
"""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from rescue.rescue_evidence_spool import sanitize_rescue_log

_INTERESTING = re.compile(
    r"(firmware|nouveau|nvidia|amdgpu|nvme|mce|edac|iommu|aer|usb|i8042|hid|"
    r"Bluetooth|ath1|iwlwifi|mt79|rtx|drm|error|fail|timeout|reset)",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_interesting_kernel_lines(
    text: str,
    *,
    max_lines: int = 200,
) -> list[str]:
    lines = []
    for raw in (text or "").splitlines():
        line = sanitize_rescue_log(raw.rstrip())
        if not line:
            continue
        if _INTERESTING.search(line):
            lines.append(line[:500])
        if len(lines) >= max_lines:
            break
    return lines


def build_kernel_excerpt_events(
    lines: Sequence[str],
    *,
    run_id: str,
    boot_id: str,
    boot_attempt: int = 0,
    boot_profile: str = "",
    boot_stage: str = "critical_modules_loaded",
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in lines:
        severity = "error" if re.search(r"error|fail|timeout|reset", line, re.I) else "info"
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "run_id": run_id,
                "boot_id": boot_id,
                "boot_attempt": boot_attempt,
                "boot_profile": boot_profile,
                "timestamp": _now_iso(),
                "monotonic_ms": int(time.monotonic() * 1000),
                "boot_stage": boot_stage,
                "device_id": "",
                "device_class": "kernel",
                "vendor_id": "",
                "product_id": "",
                "driver_expected": "",
                "driver_actual": "",
                "module_state": "",
                "firmware_state": "",
                "operational_state": "observed",
                "severity": severity,
                "issue_code": "kernel_excerpt",
                "technical_summary": line,
                "evidence_refs": [],
            }
        )
    return events


def collect_dmesg_excerpt(
    *,
    runner: Callable[[], str] | None = None,
    max_lines: int = 200,
) -> list[str]:
    if runner is not None:
        return extract_interesting_kernel_lines(runner(), max_lines=max_lines)
    try:
        import subprocess

        proc = subprocess.run(
            ["dmesg", "-T"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        return extract_interesting_kernel_lines(proc.stdout or proc.stderr or "", max_lines=max_lines)
    except (OSError, TimeoutError):
        return []
    except Exception:
        return []
