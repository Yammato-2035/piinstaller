#!/usr/bin/env python3
"""
Recovery-Modus (offlinefähig): prüft Root-System, bietet Menü für Restore/Diagnose.
Start: python3 recovery/main.py  (aus dem Projektroot)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def root_system_healthy() -> bool:
    """Heuristik: typische Root-Dateien vorhanden (prüfbar, kein Netz)."""
    return Path("/etc/os-release").is_file() and Path("/bin/sh").exists()


def run_menu_interactive() -> int:
    from core.backup_recovery_i18n import (
        K_RECOVERY_MENU_TITLE,
        K_RECOVERY_OPT_CLOUD,
        K_RECOVERY_OPT_DIAG,
        K_RECOVERY_OPT_USB,
        K_RECOVERY_ROOT_MISSING,
        tr,
    )
    from modules.recovery_transport import auto_mount_usb, connect_webdav

    if not root_system_healthy():
        print(tr(K_RECOVERY_ROOT_MISSING), file=sys.stderr)

    print(tr(K_RECOVERY_MENU_TITLE))
    print(f"  1) {tr(K_RECOVERY_OPT_USB)}")
    print(f"  2) {tr(K_RECOVERY_OPT_CLOUD)}")
    print(f"  3) {tr(K_RECOVERY_OPT_DIAG)}")
    try:
        choice = input("> ").strip()
    except EOFError:
        choice = ""

    if choice == "1":
        ok, key, path = auto_mount_usb()
        print(key, path or "")
        return 0 if ok else 1
    if choice == "2":
        url = input("WebDAV base URL: ").strip()
        user = input("User: ").strip()
        pw = input("Password: ").strip()
        ok, key, err = connect_webdav(url, user, pw)
        print(key, err or "")
        return 0 if ok else 1
    if choice == "3":
        print("diagnosis: use backend diagnosis API or logs when system is up")
        return 0

    print("no option selected")
    return 0


def main() -> int:
    return run_menu_interactive()


if __name__ == "__main__":
    raise SystemExit(main())
