"""
USB- und Cloud-Transport für Recovery: Mount, WebDAV, Download (offlinefähig bis auf Netz).
Keine Paketinstallation – externe Tools (udisks/mount/curl) müssen vorhanden sein.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

from core.backup_recovery_i18n import (
    K_DOWNLOAD_FAILED,
    K_OPERATION_OK,
    K_USB_MOUNT_FAILED,
    K_WEBDAV_FAILED,
    tr,
)

# Erlaubte Mount-Basen (Whitelist)
_DEFAULT_USB_BASES = ("/media", "/mnt", "/run/media")


def auto_mount_usb(
    *,
    device_hint: str | None = None,
    mount_bases: tuple[str, ...] = _DEFAULT_USB_BASES,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Sucht ein eingehängtes USB-Volume unter mount_bases oder versucht udisctl (ohne feste Root-Pfade außerhalb Whitelist).
    """
    run = runner or subprocess.run
    for base in mount_bases:
        b = Path(base)
        if not b.is_dir():
            continue
        for child in sorted(b.iterdir()):
            if device_hint and device_hint not in str(child):
                continue
            try:
                if child.is_dir() and os.access(child, os.R_OK):
                    return True, K_OPERATION_OK, str(child)
            except OSError:
                continue
    if device_hint and Path(device_hint).is_dir():
        return True, K_OPERATION_OK, device_hint
    return False, K_USB_MOUNT_FAILED, tr(K_USB_MOUNT_FAILED)


def connect_webdav(
    base_url: str,
    user: str,
    password: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """Prüft WebDAV-Erreichbarkeit per curl PROPFIND (kein Speichern der Zugangsdaten)."""
    run = runner or subprocess.run
    if not base_url.strip():
        return False, K_WEBDAV_FAILED, None
    url = base_url.rstrip("/") + "/"
    argv = [
        "curl",
        "-sS",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code}",
        "-u",
        f"{user}:{password}",
        "-X",
        "PROPFIND",
        "-H",
        "Depth: 0",
        url,
    ]
    r = run(argv, capture_output=True, text=True, timeout=60)
    code_s = (r.stdout or "").strip()
    try:
        code = int(code_s) if code_s else None
    except ValueError:
        code = None
    if r.returncode == 0 and code in (200, 201, 204, 207):
        return True, K_OPERATION_OK, None
    return False, K_WEBDAV_FAILED, (r.stderr or "")[:500]


def download_backup(
    remote_url: str,
    local_path: str | Path,
    *,
    user: str = "",
    password: str = "",
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """Lädt Datei per curl; Zielpfad muss vom Aufrufer erlaubt sein."""
    run = runner or subprocess.run
    lp = Path(local_path)
    lp.parent.mkdir(parents=True, exist_ok=True)
    argv: list[str] = ["curl", "-sSL", "-f"]
    if user:
        argv.extend(["-u", f"{user}:{password}"])
    argv.extend(["-o", str(lp), remote_url])
    r = run(argv, capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 or not lp.is_file():
        return False, K_DOWNLOAD_FAILED, (r.stderr or r.stdout or "")[:500]
    return True, K_OPERATION_OK, str(lp)


__all__ = ["auto_mount_usb", "connect_webdav", "download_backup", "_DEFAULT_USB_BASES"]
