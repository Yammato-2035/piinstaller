"""PI-RS-MSI-FIX-001 — read-only squashfs content checks for console shield / MSI safe-UI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version

_COMMON_MARKERS = (
    "setuphelfer_rescue_shield_console_early",
    "setuphelfer_rescue_should_auto_msi_evidence",
    "setuphelfer_rescue_tty1_clear_allowed",
    "setuphelfer_rescue_write_gui_fallback_status",
)

_BOOT_PROGRESS_FORBIDDEN = (
    'show_tty "Bootvorbereitung abgeschlossen — GUI übernimmt." 1',
    'show_tty "$msg" 1',
)

_BOOT_PROGRESS_REQUIRED = (
    "setuphelfer_rescue_shield_console_early",
    "Textmenü bereit",
    "setuphelfer_rescue_tty1_clear_allowed",
)

_LAB_SCRIPT_MARKERS = (
    "lab-rs-tel-send001-preview.sh",
    "lab-rs-tel-send001-send.sh",
)


def default_repacked_squashfs_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    version = rescue_payload_version()
    return root / "build" / "rescue" / f"filesystem.squashfs.repacked-{version}"


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


def verify_rescue_payload_msi_fix_content(squashfs_path: Path) -> dict[str, Any]:
    version_file = _unsquashfs_cat(squashfs_path, "opt/setuphelfer-rescue/VERSION").strip()
    expected = rescue_payload_version()
    common = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-common.sh")
    boot_progress = _unsquashfs_cat(squashfs_path, "usr/local/sbin/setuphelfer-rescue-boot-progress")
    listing_proc = subprocess.run(
        ["unsquashfs", "-ll", str(squashfs_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    listing = (listing_proc.stdout or "") + (listing_proc.stderr or "")

    common_markers = {name: name in common for name in _COMMON_MARKERS}
    boot_required = {token: token in boot_progress for token in _BOOT_PROGRESS_REQUIRED}
    boot_forbidden = {token: token in boot_progress for token in _BOOT_PROGRESS_FORBIDDEN}
    lab_scripts = {name: name in listing for name in _LAB_SCRIPT_MARKERS}

    content_ok = (
        listing_proc.returncode == 0
        and version_file == expected
        and all(common_markers.values())
        and all(boot_required.values())
        and not any(boot_forbidden.values())
        and all(lab_scripts.values())
    )

    return {
        "squashfs_path": str(squashfs_path),
        "version_expected": expected,
        "version_in_payload": version_file,
        "version_match": version_file == expected,
        "common_markers": common_markers,
        "boot_progress_required": boot_required,
        "boot_progress_forbidden_present": boot_forbidden,
        "lab_scripts": lab_scripts,
        "content_ok": content_ok,
    }
