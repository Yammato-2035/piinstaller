"""
Control Center API handlers (Phase E.9) — extracted from app.py.

Delegates to modules.control_center via control_center_runtime adapters.
"""

from __future__ import annotations

from fastapi import Request

from core import control_center_runtime as rt

async def get_wifi_networks():
    """Listet verfügbare WiFi-Netzwerke auf (verwendet rt.sudo_store())."""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_wifi_networks(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der WiFi-Netzwerke: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def wifi_scan_post(request: Request):
    """WiFi-Scan mit explizitem sudo-Passwort (um Session/Worker-Probleme zu umgehen)."""
    try:
        data = {}
        if "application/json" in (request.headers.get("content-type") or ""):
            try:
                data = await request.json() or {}
            except Exception:
                pass
        sudo_password = (data.get("sudo_password") or "").strip()
        if not sudo_password:
            sudo_password = (rt.sudo_store().get_password() or "")
        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
            )
        if sudo_password and not rt.sudo_store().has_password():
            rt.sudo_store().store_password(sudo_password)
        module = rt.get_control_center_module()
        return module.get_wifi_networks(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim WiFi-Scan: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_wifi_config():
    """Liest aktuelle WiFi-Konfiguration"""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_wifi_config(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen der WiFi-Konfiguration: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_wifi_status():
    """Aktuell verbundenes WLAN, Interface, Signal, WLAN aktiviert (rfkill)."""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_wifi_status(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim WiFi-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def wifi_disconnect(request: Request):
    """WLAN-Verbindung trennen."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.wifi_disconnect(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim WLAN-Trennen: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def wifi_set_enabled(request: Request):
    """WLAN aktivieren/deaktivieren (rfkill)."""
    try:
        data = await request.json()
        enabled = data.get("enabled", True)
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.wifi_set_enabled(bool(enabled), sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim WLAN aktivieren/deaktivieren: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def add_wifi_network(request: Request):
    """Fügt ein WiFi-Netzwerk hinzu"""
    try:
        data = await request.json()
        ssid = data.get("ssid", "")
        password = data.get("password", "")
        security = data.get("security", "WPA2")
        
        if not ssid:
            return rt.json_response(status_code=200, content={"status": "error", "message": "SSID erforderlich"})
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.add_wifi_network(ssid, password, security, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Hinzufügen des WiFi-Netzwerks: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def wifi_connect(request: Request):
    """Verbindung zu einem konfigurierten WLAN-Netzwerk herstellen"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        ssid = (data.get("ssid") or "").strip()
        if not ssid:
            return rt.json_response(status_code=200, content={"status": "error", "message": "SSID erforderlich"})
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.wifi_connect(ssid, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim WLAN-Verbinden: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_ssh_status():
    """Prüft SSH-Status"""
    try:
        module = rt.get_control_center_module()
        return module.get_ssh_status()
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen des SSH-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_ssh_enabled(request: Request):
    """Aktiviert/deaktiviert SSH"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.set_ssh_enabled(enabled, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen des SSH-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def start_ssh(request: Request):
    """SSH-Dienst starten"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.start_ssh_service(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim SSH-Start: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_vnc_status():
    """Prüft VNC-Status"""
    try:
        module = rt.get_control_center_module()
        return module.get_vnc_status()
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen des VNC-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_vnc_enabled(request: Request):
    """Aktiviert/deaktiviert VNC"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        password = data.get("password", "")
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.set_vnc_enabled(enabled, password, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen des VNC-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def start_vnc(request: Request):
    """VNC-Dienst starten"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.start_vnc_service(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim VNC-Start: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_keyboard_layout():
    """Liest Tastatur-Layout"""
    try:
        module = rt.get_control_center_module()
        return module.get_keyboard_layout()
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen des Tastatur-Layouts: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_keyboard_layout(request: Request):
    """Setzt Tastatur-Layout"""
    try:
        data = await request.json()
        layout = data.get("layout", "de")
        variant = data.get("variant", "")
        options = data.get("options", "")
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.set_keyboard_layout(layout, variant, options, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen des Tastatur-Layouts: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_locale():
    """Liest Locale-Einstellungen"""
    try:
        module = rt.get_control_center_module()
        return module.get_locale()
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen der Locale: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_locale(request: Request):
    """Setzt Locale und Timezone"""
    try:
        data = await request.json()
        locale = data.get("locale", "de_DE.UTF-8")
        timezone = data.get("timezone", "")
        
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.set_locale(locale, timezone, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen der Locale: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_desktop_settings():
    """Liest Desktop-Einstellungen"""
    try:
        module = rt.get_control_center_module()
        return module.get_desktop_settings()
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen der Desktop-Einstellungen: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_desktop_boot_target():
    """Liest das Boot-Ziel (Desktop vs. Kommandozeile)."""
    try:
        module = rt.get_control_center_module()
        return module.get_boot_target()
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen des Boot-Ziels: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_desktop_boot_target(request: Request):
    """Setzt das Boot-Ziel: graphical (Desktop) oder multi-user (Kommandozeile)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        target = data.get("target", "").strip()
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        if not sudo_password:
            return rt.json_response(
                status_code=200,
                content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
            )
        module = rt.get_control_center_module()
        return module.set_boot_target(target, sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen des Boot-Ziels: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_display_settings():
    """Liest Display-Einstellungen (xrandr: Outputs, Modi, Rotation)."""
    try:
        module = rt.get_control_center_module()
        return module.get_display_settings()
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen der Display-Einstellungen: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_display_settings(request: Request):
    """Setzt Display (xrandr: Output, Modus, Wiederholrate, Rotation). Kein sudo."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        output = (data.get("output") or "").strip()
        mode = (data.get("mode") or "").strip()
        rate = data.get("rate")
        if rate is not None:
            try:
                rate = float(rate)
            except (TypeError, ValueError):
                rate = None
        rotation = (data.get("rotation") or "").strip() or "normal"
        module = rt.get_control_center_module()
        return module.set_display_settings(
            output=output or "HDMI-1",
            mode=mode or "1920x1080",
            rate=rate,
            rotation=rotation,
            sudo_password="",
        )
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen der Display-Einstellungen: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_display_telemetry_settings():
    """Liest OLED/Display-Telemetrieeinstellungen inkl. Runner-Status. Nutzt ggf. Sudo-Passwort für I2C-OLED-Erkennung."""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_display_telemetry_settings(sudo_password=sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Lesen der OLED-Telemetrie: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_display_telemetry_settings(request: Request):
    """Speichert OLED/Display-Telemetrieeinstellungen."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        target = str(data.get("target") or "auto")
        metrics = data.get("metrics") if isinstance(data.get("metrics"), dict) else None
        enabled = data.get("enabled")
        autostart = data.get("autostart")
        if enabled is not None:
            enabled = bool(enabled)
        if autostart is not None:
            autostart = bool(autostart)
        sudo_password = (data.get("sudo_password") or "").strip() or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.set_display_telemetry_settings(
            target=target,
            metrics=metrics,
            enabled=enabled,
            autostart=autostart,
            sudo_password=sudo_password,
        )
    except Exception as e:
        rt.logger().error(f"Fehler beim Speichern der OLED-Telemetrie: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_display_telemetry_runner(request: Request):
    """Startet/stoppt/neustartet den OLED-Runner."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        action = str((data or {}).get("action") or "restart").strip().lower()
        module = rt.get_control_center_module()
        if action == "start":
            return module.start_display_telemetry_runner()
        if action == "stop":
            return module.stop_display_telemetry_runner()
        if action == "restart":
            module.stop_display_telemetry_runner()
            return module.start_display_telemetry_runner()
        return {"status": "error", "message": "Ungültige Aktion. Erlaubt: start, stop, restart."}
    except Exception as e:
        rt.logger().error(f"Fehler beim Steuern des OLED-Runners: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_printers():
    """Listet Drucker auf"""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_printers(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Drucker: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_scanners():
    """Listet SANE-Scanner auf"""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_scanners(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Scanner: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_performance():
    """Performance: CPU-Governor, GPU/Overclocking (config.txt), Swap."""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_performance(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Abrufen der Performance-Daten: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def set_performance(request: Request):
    """Performance setzen: Governor, GPU-Mem, Overclocking, Swap-Größe."""
    try:
        try:
            data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        except Exception:
            data = {}
        data = data or {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        if not sudo_password:
            sudo_ok = rt.run_command("sudo -n true", sudo=False)
            if not sudo_ok.get("success"):
                return rt.json_response(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        module = rt.get_control_center_module()
        swap_mb = data.get("swap_size_mb")
        if swap_mb is not None:
            try:
                swap_mb = int(swap_mb)
            except (TypeError, ValueError):
                swap_mb = None
        result = module.set_performance(
            sudo_password=sudo_password,
            governor=data.get("governor"),
            gpu_mem=data.get("gpu_mem"),
            arm_freq=data.get("arm_freq"),
            over_voltage=data.get("over_voltage"),
            force_turbo=data.get("force_turbo"),
            swap_size_mb=swap_mb,
        )
        return result
    except Exception as e:
        rt.logger().error(f"Fehler beim Setzen der Performance: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def get_bluetooth_status():
    """Bluetooth-Status: aktiviert/deaktiviert, verbundene Geräte."""
    try:
        sudo_password = (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.get_bluetooth_status(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Bluetooth-Status: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def bluetooth_scan(request: Request):
    """Bluetooth-Geräte scannen."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.bluetooth_scan(sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Bluetooth-Scan: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})



async def bluetooth_set_enabled(request: Request):
    """Bluetooth aktivieren/deaktivieren."""
    try:
        data = await request.json()
        enabled = data.get("enabled", True)
        sudo_password = data.get("sudo_password", "") or (rt.sudo_store().get_password() or "")
        module = rt.get_control_center_module()
        return module.bluetooth_set_enabled(bool(enabled), sudo_password)
    except Exception as e:
        rt.logger().error(f"Fehler beim Bluetooth aktivieren/deaktivieren: {str(e)}", exc_info=True)
        return rt.json_response(status_code=200, content={"status": "error", "message": str(e)})
