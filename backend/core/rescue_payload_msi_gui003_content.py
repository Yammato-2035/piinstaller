"""PI-RS-MSI-GUI-003 — read-only squashfs content checks for TUI console isolation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.rescue_payload_msi_gui002_content import verify_rescue_payload_msi_gui002_content
from core.rescue_payload_version import rescue_payload_version
from core.rescue_payload_version_carriers import verify_payload_version_carriers

_GUI003_MARKERS = (
    "resolve_rescue_boot_profile",
    "tui_mode_selected",
    "rescue_boot_timeline",
    "rescue_console_ownership",
    "rescue_session_evidence",
    "boot_progress_tty_write_allowed",
    "RESCUE_CONSOLE_WRITE_BLOCKED_TUI_OWNED",
    "tty1_write_allowed",
    "init_boot_session",
    "stale_evidence_detected",
)

_BOOT_PROGRESS_MARKERS = (
    "_load_plan",
    "setuphelfer_rescue_boot_progress_tty_write_allowed",
    "tui_mode_selected",
)


def _unsquashfs_cat(squashfs_path: Path, member: str) -> str:
    proc = subprocess.run(
        ["unsquashfs", "-force", "-no-xattrs", "-cat", str(squashfs_path), member],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def verify_rescue_payload_msi_gui003_content(squashfs_path: Path) -> dict[str, Any]:
    base = verify_rescue_payload_msi_gui002_content(squashfs_path)
    expected = rescue_payload_version()
    common = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-common.sh")
    boot_progress = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-boot-progress")
    timeline = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/backend/core/rescue_boot_timeline.py")
    ownership = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/backend/core/rescue_console_ownership.py")
    session = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/backend/core/rescue_session_evidence.py")
    profile = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/backend/core/rescue_msi_boot_profile.py")
    carriers = verify_payload_version_carriers(squashfs_path, expected_version=expected)

    backend_blob = "\n".join((timeline, ownership, session, profile))
    gui003_markers = {name: name in backend_blob or name in common or name in boot_progress for name in _GUI003_MARKERS}
    boot_markers = {name: name in boot_progress or name in timeline for name in _BOOT_PROGRESS_MARKERS}

    msi_tui_only = "boot_mode" in profile and "tui_mode_selected" in timeline
    msi_x11_block = "gui_progress_allowed" in profile and (
        "tui_mode_selected" in timeline or "tui_mode_selected" in boot_progress
    )
    tty1_guard = "boot_progress_write_allowed" in ownership and "setuphelfer_rescue_boot_progress_tty_write_allowed" in common
    session_isolation = "init_boot_session" in session and "init_boot_session" in common
    stale_guard = "stale_evidence_detected" in session and "evaluate_evidence_freshness" in session

    content_ok = (
        base.get("content_ok") is True
        and carriers.get("all_version_carriers_match") is True
        and all(gui003_markers.values())
        and all(boot_markers.values())
        and msi_tui_only
        and msi_x11_block
        and tty1_guard
        and session_isolation
        and stale_guard
    )

    return {
        **base,
        **carriers,
        "gui003_markers": gui003_markers,
        "boot_progress_markers": boot_markers,
        "msi_tui_only_mode_present": msi_tui_only,
        "msi_x11_progress_block_present": msi_x11_block,
        "tty1_ownership_guard_present": tty1_guard,
        "session_isolation_present": session_isolation,
        "stale_evidence_guard_present": stale_guard,
        "content_ok": content_ok,
        "version_expected": expected,
    }
