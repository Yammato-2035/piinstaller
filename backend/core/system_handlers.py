"""
System API handlers (Phase E.10) — paths, devices, terminal probe, reboot, packagekit.

Extracted from app.py; delegates via system_runtime adapters.
"""

from __future__ import annotations

import os
import shutil

import psutil
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


async def get_service_conflicts():
    """Lesend: parallele pi-installer-/Setuphelfer-Dienste, Port-8000-Inhaber, Empfehlungen (keine Stop-Aktion)."""
    from core.service_conflict_guard import build_service_conflict_report

    try:
        port = int(os.environ.get("PI_INSTALLER_BACKEND_PORT", "8000"))
    except ValueError:
        port = 8000
    return {"status": "success", **build_service_conflict_report(port=port)}


async def get_system_resources():
    """Ressourcen-Management (Milestone 3): RAM, Swap, Temperatur für Pi-Optimierung und App-Store-Hinweise."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.2)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ram_total_gb = round(memory.total / (1024 ** 3), 1)
        ram_available_gb = round(memory.available / (1024 ** 3), 1)
        swap_total_mb = round(swap.total / (1024 ** 2), 0)
        swap_used_mb = round(swap.used / (1024 ** 2), 0)
        cpu_temp = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            cpu_temp = rt.get_cpu_temp()
        temperature_warning = cpu_temp is not None and cpu_temp >= 80
        swap_recommended = ram_total_gb < 2
        return {
            "status": "success",
            "cpu": cpu_percent,
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_available_gb,
            "ram_percent": memory.percent,
            "swap_total_mb": swap_total_mb,
            "swap_used_mb": swap_used_mb,
            "swap_percent": round(swap.percent, 1) if swap.total else 0,
            "temperature_c": cpu_temp,
            "temperature_warning": temperature_warning,
            "swap_recommended": swap_recommended,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_installed_packages():
    """Installierte Pakete mit Details"""
    try:
        return {
            "status": "success",
            "packages": rt.get_installed_packages_list(),
        }
    except Exception as e:
        raise rt.http_exception(status_code=500, detail=str(e))


async def get_running_processes_endpoint():
    """Laufende Prozesse"""
    try:
        return {
            "status": "success",
            "processes": rt.list_running_processes(),
        }
    except Exception as e:
        raise rt.http_exception(status_code=500, detail=str(e))


async def get_security_config_endpoint(request: Request):
    """Sicherheitseinstellungen"""
    try:
        sudo_password = request.query_params.get("sudo_password", "")
        if sudo_password and not rt.sudo_store().has_password():
            rt.sudo_store().store_password(sudo_password)
            rt.logger().info("💾 Sudo-Passwort im Store gespeichert (via security-config endpoint)")

        return {
            "status": "success",
            "config": rt.get_security_config(),
        }
    except Exception as e:
        raise rt.http_exception(status_code=500, detail=str(e))


async def get_system_updates():
    """Verfügbare System-Updates (für Dashboard-Anzeige)"""
    try:
        data = rt.get_updates_categorized()
        return {
            "status": "success",
            "total": data["total"],
            "categories": data["categories"],
            "updates": data["updates"],
        }
    except Exception as e:
        return {
            "status": "error",
            "total": 0,
            "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0},
            "updates": [],
            "message": str(e),
        }
