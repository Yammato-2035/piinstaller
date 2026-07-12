"""PI-RS-MSI-GUI-002 — read-only squashfs content checks for MSI GUI disable."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.rescue_payload_msi_fix_content import verify_rescue_payload_msi_fix_content
from core.rescue_payload_version import rescue_payload_version

_GUI002_MARKERS = (
    "setuphelfer_rescue_should_disable_gui_for_msi_compat",
    "setuphelfer_rescue_write_gui_availability_status",
    "setuphelfer_rescue_gui_disabled_message",
    "setuphelfer_rescue_write_gui_blocked_msi_status",
    "disabled_msi_compat_nomodeset",
    "Grafische Oberfläche auf diesem Gerät im MSI-Kompatibilitätsmodus nicht verfügbar",
    "GUI_VT_BLOCKED",
    "GUI_WATCHDOG_BLOCKED",
)

_TUI_GUARD_MARKERS = (
    "setuphelfer_rescue_should_disable_gui_for_msi_compat",
    "setuphelfer_rescue_gui_disabled_message",
    "setuphelfer_rescue_write_gui_blocked_msi_status",
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


def verify_rescue_payload_msi_gui002_content(squashfs_path: Path) -> dict[str, Any]:
    base = verify_rescue_payload_msi_fix_content(squashfs_path)
    common = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-common.sh")
    tui = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-tui")
    if not tui.strip():
        tui = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-tui.sh")
    watchdog = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-gui-watchdog")
    if not watchdog.strip():
        watchdog = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-gui-watchdog.sh")

    gui_markers = {name: name in common or name in tui or name in watchdog for name in _GUI002_MARKERS}
    tui_guard = {name: name in tui for name in _TUI_GUARD_MARKERS}
    watchdog_blocks_openvt = "GUI_WATCHDOG_BLOCKED" in watchdog and "openvt=false" in watchdog
    run_on_kiosk_blocks = "GUI_VT_BLOCKED" in common and "openvt=false" in common

    content_ok = (
        base.get("content_ok") is True
        and all(gui_markers.values())
        and all(tui_guard.values())
        and watchdog_blocks_openvt
        and run_on_kiosk_blocks
    )

    return {
        **base,
        "gui002_markers": gui_markers,
        "tui_guard_markers": tui_guard,
        "watchdog_blocks_msi_gui": watchdog_blocks_openvt,
        "run_on_kiosk_vt_blocks_msi_gui": run_on_kiosk_blocks,
        "content_ok": content_ok,
        "version_expected": rescue_payload_version(),
    }
