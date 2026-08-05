"""
Storage baseline diagnostics shared across HDD/SATA-SSD/NVMe — read-only.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 6.

Common checks used by every storage-device baseline builder
(``hdd_baseline_diagnostics.py``, ``sata_ssd_baseline_diagnostics.py``,
``nvme_baseline_diagnostics.py``): kernel I/O error scanning, tool
availability (``smartctl``/``nvme-cli``), and a small common-state summary.
Device-class-specific SMART/NVMe attribute parsing lives in the per-class
modules — this module intentionally stays generic.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any, Callable

STORAGE_BASELINE_DIAGNOSTICS_VERSION = 1

Runner = Callable[..., "subprocess.CompletedProcess[str]"] | None


def _run_tool(argv: list[str], *, runner: Runner = None, timeout: int = 15) -> tuple[str, bool]:
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


def scan_kernel_storage_errors(device_id: str, dmesg_text: str | None = None, *, runner: Runner = None) -> dict[str, Any]:
    """Scan kernel log text for this device's I/O errors, reset/timeout
    messages, and link errors. ``device_id`` is matched as a plain
    substring (e.g. ``sda`` or an NVMe *controller* name like ``nvme0`` —
    callers strip namespace suffixes themselves, since kernel messages
    usually name the controller, not the namespace block device)."""
    missing_tools: list[str] = []
    text = dmesg_text
    if text is None:
        text, present = _run_tool(["dmesg"], runner=runner)
        if not present:
            missing_tools.append("dmesg")
    text = text or ""

    name_marker = re.escape(device_id)
    device_lines = [line for line in text.splitlines() if re.search(name_marker, line)]
    device_text = "\n".join(device_lines)

    io_error_count = len(re.findall(r"I/O error|Buffer I/O error|end_request: I/O error", device_text, re.IGNORECASE))
    reset_timeout_count = len(re.findall(r"reset|timeout|timed out", device_text, re.IGNORECASE))
    link_error_count = len(re.findall(r"link is down|link reset|ata error|CRC error", device_text, re.IGNORECASE))

    return {
        "io_error_count": io_error_count,
        "reset_timeout_count": reset_timeout_count,
        "link_error_count": link_error_count,
        "missing_tools": missing_tools,
    }


def check_tool_availability(tool: str, *, runner: Runner = None) -> bool:
    """True only if the tool actually ran (``--version``/``version`` probe).
    Never installs the tool — a missing tool simply yields ``False``."""
    probe_args = {"smartctl": ["smartctl", "--version"], "nvme": ["nvme", "version"]}.get(tool, [tool, "--version"])
    _, present = _run_tool(probe_args, runner=runner, timeout=5)
    return present


def summarize_common_device_state(
    *, device_id: str, capacity_bytes: int | None = None, mountpoints: tuple[str, ...] = ()
) -> dict[str, Any]:
    return {
        "device_id": device_id,
        "capacity_bytes": capacity_bytes,
        "mountpoints": list(mountpoints),
        "is_mounted": len(mountpoints) > 0,
    }


def build_storage_baseline_diagnostics() -> dict[str, Any]:
    return {
        "module_version": STORAGE_BASELINE_DIAGNOSTICS_VERSION,
        "module": "core.storage_baseline_diagnostics",
        "read_only": True,
        "writes_allowed": False,
        "installs_tools": False,
        "starts_smart_self_test": False,
    }


__all__ = [
    "STORAGE_BASELINE_DIAGNOSTICS_VERSION",
    "scan_kernel_storage_errors",
    "check_tool_availability",
    "summarize_common_device_state",
    "build_storage_baseline_diagnostics",
]
