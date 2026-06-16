"""
System API handlers (Phase E.10) — paths, devices, terminal probe, reboot, packagekit.

Extracted from app.py; delegates via system_runtime adapters.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess

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


async def system_status():
    """
    Zentrale Systemstatus-API.
    Liefert Ampelwerte für Backup, Restore, Security, Updates.
    """
    from core.system_status_facade import build_system_status

    try:
        return await asyncio.to_thread(build_system_status)
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen des Systemstatus: {e}", exc_info=True)
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "api_status": "error",
                "message": str(e),
                "data": {},
            },
        )


async def get_freenove_detection():
    """Erkennt Freenove Computer Case Kit Pro – für TFT-Bereich im App Store."""
    from core.hardware_discovery import detect_freenove_case
    data = detect_freenove_case(run_command_fn=rt.run_command)
    return {"status": "success", **data}


async def get_asus_fan_profiles():
    """Holt verfügbare ASUS ROG Lüfter-Profile"""
    try:
        result = rt.get_asus_fan_profiles()
        return rt.json_response(status_code=200, content=result)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Lüfter-Profile: {str(e)}", exc_info=True)
        return rt.json_response(status_code=500, content={"available": False, "profiles": [], "error": str(e)})


async def get_asus_fan_status():
    """Holt aktuellen ASUS ROG Lüfter-Status"""
    try:
        result = rt.get_asus_fan_status()
        return rt.json_response(status_code=200, content=result)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen des Lüfter-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=500, content={"available": False, "status": None, "error": str(e)})


async def set_asus_fan_profile(request: Request):
    """Setzt ASUS ROG Lüfter-Profil (Performance, Balanced, Quiet)"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        profile = data.get("profile", "")
        if not profile:
            return rt.json_response(status_code=400, content={"success": False, "error": "Profil-Parameter fehlt"})
        
        # Hole sudo_password aus Request oder Store
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        
        # Prüfe ob sudo benötigt wird
        if not sudo_password:
            sudo_test = rt.run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return rt.json_response(
                    status_code=200,
                    content={
                        "success": False,
                        "error": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # Speichere sudo_password im Store falls vorhanden
        if sudo_password and not rt.sudo_store().has_password():
            rt.sudo_store().store_password(sudo_password)
        
        result = rt.set_asus_fan_profile(profile, sudo_password)
        if result.get("success"):
            return rt.json_response(status_code=200, content=result)
        else:
            return rt.json_response(status_code=400, content=result)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen des Lüfter-Profils: {str(e)}", exc_info=True)
        return rt.json_response(status_code=500, content={"success": False, "error": str(e)})


async def get_asus_rog_detection():
    """Prüft ob ASUS ROG System erkannt wurde und ob asusctl verfügbar ist"""
    try:
        is_rog = rt.is_asus_rog_system()
        has_asusctl = rt.is_asusctl_available()
        return rt.json_response(status_code=200, content={
            "is_asus_rog": is_rog,
            "asusctl_available": has_asusctl,
            "can_control_fans": is_rog and has_asusctl
        })
    except Exception as e:
        rt.logger().error(f"Fehler bei ASUS ROG Erkennung: {str(e)}", exc_info=True)
        return rt.json_response(status_code=500, content={"error": str(e)})


async def run_update_in_terminal():
    """Manuelle Update-Anleitung. Backend startet keine grafische Sitzung und kein apt.

    - Kein subprocess, kein Terminal, kein sudo, kein pkexec.
    - Antwort ist immer `status=manual_required` (HTTP 200).
    """
    commands = ["sudo apt update", "sudo apt upgrade"]
    copyable = " && ".join(commands)
    return rt.json_response(
        status_code=200,
        content={
            "status": "manual_required",
            "code": "updates.manual_terminal_required",
            "message": (
                "Setuphelfer fuehrt aus Sicherheitsgruenden keine unbeaufsichtigten "
                "Systemupdates aus. Bitte ein Terminal manuell oeffnen und die "
                "Befehle ausfuehren — nicht waehrend Backup/Restore/Paketmanager-Vorgang."
            ),
            "commands": commands,
            "copyable_command": copyable,
            "blocked_auto_execution": True,
            "reason": "systemd_service_has_no_graphical_session_and_auto_apt_upgrade_is_unsafe",
            "br001_warning": (
                "Vor einem BR-001-Backup keine Updates starten — Paketmanager-Locks "
                "koennen Backups blockieren."
            ),
        },
    )


async def run_mixer(request: Request):
    """Startet einen grafischen Mixer (pavucontrol oder qpwgraph) im Hintergrund.
    Läuft auf dem Rechner, auf dem das Backend läuft – bei lokalem Zugriff öffnet sich das Fenster dort."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        app_name = (data.get("app") or "").strip().lower()
        if app_name not in ALLOWED_MIXER_APPS:
            return rt.json_response(
                status_code=200,
                content={"status": "error", "message": f"Ungültige App. Erlaubt: {', '.join(ALLOWED_MIXER_APPS)}"}
            )
        import shutil
        path = shutil.which(app_name)
        if not path:
            return rt.json_response(
                status_code=200,
                content={"status": "error", "message": f"'{app_name}' nicht gefunden. Bitte installieren (z. B. apt install {app_name})."}
            )
        # GUI-Apps brauchen DISPLAY (Backend läuft oft ohne Grafik-Umgebung)
        env = dict(os.environ)
        if not env.get("DISPLAY"):
            env["DISPLAY"] = ":0"
        # GTK-A11y-Warnung unterdrücken (org.a11y.Bus nicht vorhanden)
        if app_name == "pavucontrol":
            env["GTK_A11Y"] = "none"
        subprocess.Popen(
            [path],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        return {"status": "success", "message": f"{app_name} gestartet"}
    except Exception as e:
        rt.logger().exception("run-mixer fehlgeschlagen")
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})


async def install_mixer_packages(request: Request):
    """Installiert pavucontrol und qpwgraph (apt-get update, dann apt-get install). Benötigt sudo."""
    copyable = "sudo apt-get update && sudo apt-get install -y pavucontrol qpwgraph"
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = (data.get("sudo_password", "") or (rt.sudo_store().get_password() or "") or "").strip()
        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Sudo-Passwort erforderlich.",
                    "requires_sudo_password": True,
                    "copyable_command": copyable,
                }
            )
        if not rt.sudo_store().has_password():
            rt.sudo_store().store_password(sudo_password)
        # Schritt 1: apt-get update
        result_update = rt.run_apt_update(sudo_password)
        if not result_update.get("success"):
            err = (result_update.get("stderr") or result_update.get("stdout") or result_update.get("error") or "").strip()
            if result_update.get("error") == "Command timeout":
                err = "Zeitüberschreitung beim Paketquellen-Update."
            elif not err:
                err = "apt-get update ist fehlgeschlagen (keine Ausgabe)."
            rt.logger().warning("install-mixer-packages apt-get update fehlgeschlagen: %s", err[:400])
            return rt.json_response(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Paketquellen-Update fehlgeschlagen: {err[:500]}",
                    "copyable_command": copyable,
                }
            )
        # Schritt 2: apt-get install
        result_install = rt.run_apt_install_mixer(sudo_password)
        if result_install.get("success"):
            return {"status": "success", "message": "pavucontrol und qpwgraph installiert"}
        err = (result_install.get("stderr") or result_install.get("stdout") or result_install.get("error") or "").strip()
        if result_install.get("error") == "Command timeout":
            err = "Zeitüberschreitung bei der Installation."
        elif not err:
            err = "apt-get install ist fehlgeschlagen (keine Ausgabe)."
        rt.logger().warning("install-mixer-packages apt-get install fehlgeschlagen: %s", err[:400])
        return rt.json_response(
            status_code=200,
            content={
                "status": "error",
                "message": err[:600],
                "copyable_command": copyable,
            }
        )
    except Exception as e:
        rt.logger().exception("install-mixer-packages fehlgeschlagen")
        return rt.json_response(
            status_code=200,
            content={"status": "error", "message": str(e)[:500], "copyable_command": copyable}
        )
