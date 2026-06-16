"""
System API handlers (Phase E.10) — paths, devices, terminal probe, reboot, packagekit.

Extracted from app.py; delegates via system_runtime adapters.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import Request

from core import system_runtime as rt

async def get_system_paths():
    """Prüft kritische Pfade (NVMe-Boot, Konfiguration). Hilft bei Pfad-Problemen nach Laufwerkswechsel."""
    _cfg = rt.get_config_dir() / "config.json"
    _bk = rt.get_config_dir() / "backup.json"
    paths = {
        "config_etc": str(_cfg),
        "config_etc_exists": _cfg.exists(),
        "config_home": str(Path.home() / ".config" / "setuphelfer" / "config.json"),
        "backup_json": str(_bk),
        "boot_firmware": "/boot/firmware",
        "boot_firmware_config": "/boot/firmware/config.txt",
        "boot_firmware_cmdline": "/boot/firmware/cmdline.txt",
        "boot_firmware_exists": Path("/boot/firmware").exists(),
        "mnt_backups": "/mnt/setuphelfer/backups",
        "mnt_backups_exists": Path("/mnt/setuphelfer/backups").exists(),
        "root_mount": rt.root_mount_device(),
    }
    return {"status": "success", "paths": paths}



async def get_system_devices():
    """Klassifizierte Blockgeräte (lsblk): nur Information, keine automatische Auswahl."""
    try:
        from core.storage_facade import list_devices_for_api

        return {"status": "success", "devices": list_devices_for_api()}
    except Exception as e:
        return rt.json_response(
            status_code=500,
            content={"status": "error", "message": str(e), "devices": []},
        )



async def check_terminal_available():
    """Prüft, ob ein Terminal zum Öffnen verfügbar ist (für Anzeige des Buttons)."""
    import shutil
    for name in ["gnome-terminal", "gnome-terminal.wrapper", "xfce4-terminal", "konsole", "xterm", "mate-terminal", "lxterminal"]:
        if shutil.which(name):
            return {"available": True, "terminal": name}
    return {"available": False, "terminal": None}


ALLOWED_MIXER_APPS = ("pavucontrol", "qpwgraph")



async def reboot_system(request: Request):
    """Startet das System neu"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        if not sudo_password:
            return rt.json_response(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        
        result = rt.run_command("sudo -S reboot", sudo=True, sudo_password=sudo_password, timeout=5)
        if result.get("success"):
            return {"status": "success", "message": "Neustart gestartet"}
        else:
            return rt.json_response(status_code=200, content={"status": "error", "message": result.get("stderr") or "Neustart fehlgeschlagen"})
    except Exception as e:
        rt.logger().error(f"Fehler beim Neustart: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def stop_packagekit(request: Request):
    """Stoppt PackageKit manuell, um apt-get-Konflikte zu vermeiden."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        rt.ensure_packagekit_stopped(sudo_password)
        return {"status": "success", "message": "PackageKit gestoppt (falls aktiv)"}
    except Exception as e:
        rt.logger().error(f"Fehler beim Stoppen von PackageKit: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})





