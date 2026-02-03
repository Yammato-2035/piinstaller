"""
Raspberry Pi Control Center Modul
Verwaltet System-Einstellungen wie WLAN, Desktop, Display, Drucker, SSH, VNC, etc.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import json
import re
import os


class ControlCenterModule:
    """Raspberry Pi Control Center Einstellungen verwalten"""
    
    def __init__(self):
        self.wpa_supplicant_file = Path("/etc/wpa_supplicant/wpa_supplicant.conf")
        self.ssh_enable_file = Path("/boot/ssh")  # SSH aktivieren
        self.vnc_config_file = Path("/home/pi/.vnc/config")  # VNC Konfiguration
        self.x11_keyboard_file = Path("/etc/default/keyboard")
        self.locale_file = Path("/etc/locale.gen")
        self.locale_conf_file = Path("/etc/default/locale")
        self.desktop_config_dir = Path("/home/pi/.config")
        self.printers_config_file = Path("/etc/cups/printers.conf")

    def _get_wifi_interface(self, sudo_password: str = "") -> str:
        """Ermittelt die WiFi-Schnittstelle (wlan0, wlan1, …). Pi prüft zuerst selbst."""
        # 1. iw dev (zeigt Wireless-Interfaces)
        try:
            r = subprocess.run(
                ["iw", "dev"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0 and r.stdout:
                for line in (r.stdout or "").strip().split("\n"):
                    line = line.strip()
                    if line.startswith("Interface "):
                        iface = line.split(maxsplit=1)[1].strip()
                        if iface and (iface.startswith("wlan") or iface.startswith("wlp")):
                            return iface
        except FileNotFoundError:
            pass
        except Exception:
            pass
        # 2. ip link | grep -E 'wlan|wlp'
        try:
            r = subprocess.run(
                ["sh", "-c", "ip -o link show | awk -F': ' '{print $2}' | grep -E '^wlan|^wlp' | head -1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0 and (r.stdout or "").strip():
                return (r.stdout or "").strip().split("\n")[0].strip()
        except Exception:
            pass
        return "wlan0"

    def get_wifi_networks(self, sudo_password: str = "") -> Dict[str, Any]:
        """Listet verfügbare WiFi-Netzwerke auf (iwlist oder nmcli-Fallback)."""
        def parse_iwlist(out: str) -> list:
            networks = []
            current = {}
            for line in (out or "").split("\n"):
                line = line.strip()
                if "ESSID:" in line:
                    essid = line.split("ESSID:")[1].strip().strip('"')
                    if essid:
                        current["ssid"] = essid
                elif "Encryption key:" in line:
                    current["encrypted"] = "on" in line.lower()
                elif "IE: IEEE 802.11i/WPA2" in line:
                    current["security"] = "WPA2"
                elif "IE: WPA" in line:
                    current["security"] = "WPA"
                elif current and "Quality=" in line:
                    m = re.search(r"Quality=(\d+)/(\d+)", line)
                    if m:
                        q, mx = int(m.group(1)), int(m.group(2))
                        current["signal_strength"] = int((q / mx) * 100) if mx else 0
                    if current.get("ssid"):
                        networks.append(current)
                        current = {}
            return networks

        err_msg: Optional[str] = None
        iface = self._get_wifi_interface(sudo_password)
        # Interface evtl. hochfahren (unterstützt Scan), nur mit sudo
        if sudo_password:
            _stdin = (sudo_password + "\n").encode("utf-8")
            try:
                subprocess.run(
                    ["sudo", "-S", "ip", "link", "set", iface, "up"],
                    input=_stdin,
                    capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass
        # 1. iwlist <iface> scan (mit sudo wenn Passwort)
        try:
            cmd = ["iwlist", iface, "scan"]
            kw: dict = {"capture_output": True, "text": True, "timeout": 15}
            if sudo_password:
                cmd = ["sudo", "-S", "iwlist", iface, "scan"]
                kw["input"] = sudo_password + "\n"
            r = subprocess.run(cmd, **kw)
            out = (r.stdout or "").strip()
            err = (r.stderr or "").strip()
            if r.returncode == 0 and ("Cell " in out or "ESSID:" in out):
                return {"status": "success", "networks": parse_iwlist(out), "interface": iface}
            err_msg = (err or f"iwlist exit {r.returncode}") + f" (Interface: {iface})"
        except FileNotFoundError:
            err_msg = "iwlist nicht gefunden"
        except subprocess.TimeoutExpired:
            err_msg = "iwlist Zeitüberschreitung"
        except Exception as e:
            err_msg = str(e)

        # 2. Fallback: nmcli dev wifi list
        try:
            r = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0 and (r.stdout or "").strip():
                lines = [x for x in (r.stdout or "").strip().split("\n") if x]
                seen: set = set()
                networks = []
                for line in lines:
                    parts = line.split(":", 2)
                    ssid = (parts[0] if len(parts) > 0 else "").strip()
                    if not ssid or ssid in seen:
                        continue
                    seen.add(ssid)
                    sig = 0
                    if len(parts) > 1 and parts[1].isdigit():
                        sig = int(parts[1])
                    sec = (parts[2] if len(parts) > 2 else "").strip()
                    networks.append({
                        "ssid": ssid,
                        "signal_strength": sig,
                        "security": "WPA2" if sec else "",
                        "encrypted": bool(sec),
                    })
                return {"status": "success", "networks": networks, "interface": iface}
        except FileNotFoundError:
            pass
        except Exception:
            pass

        return {
            "status": "error",
            "message": f"Fehler beim Scannen: {err_msg or 'iwlist und nmcli fehlgeschlagen'} (Interface: {iface})",
            "interface": iface,
        }
    
    def get_wifi_config(self, sudo_password: str = "") -> Dict[str, Any]:
        """Liest aktuelle WiFi-Konfiguration"""
        try:
            if not self.wpa_supplicant_file.exists():
                return {
                    "status": "success",
                    "networks": []
                }
            
            content = ""
            try:
                with open(self.wpa_supplicant_file, 'r') as f:
                    content = f.read()
            except PermissionError:
                if sudo_password:
                    result = subprocess.run(
                        ["sudo", "-S", "cat", str(self.wpa_supplicant_file)],
                        input=sudo_password + '\n',
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        content = result.stdout
            
            networks = []
            current_network = {}
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('network={'):
                    current_network = {}
                elif line.startswith('ssid='):
                    current_network['ssid'] = line.split('=', 1)[1].strip().strip('"')
                elif line.startswith('psk='):
                    current_network['password'] = line.split('=', 1)[1].strip().strip('"')
                elif line.startswith('key_mgmt='):
                    current_network['security'] = line.split('=', 1)[1].strip()
                elif line == '}':
                    if current_network:
                        networks.append(current_network)
                        current_network = {}
            
            return {
                "status": "success",
                "networks": networks,
                "interface": self._get_wifi_interface(sudo_password),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler beim Lesen: {str(e)}",
            }
    
    def add_wifi_network(self, ssid: str, password: str, security: str = "WPA2", sudo_password: str = "") -> Dict[str, Any]:
        """Fügt ein WiFi-Netzwerk hinzu"""
        try:
            # Backup erstellen (stdin als Bytes – text=True kann memoryview-Fehler verursachen)
            _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
            if self.wpa_supplicant_file.exists():
                subprocess.run(
                    ["sudo", "-S", "cp", str(self.wpa_supplicant_file), str(self.wpa_supplicant_file) + ".backup"],
                    input=_stdin,
                    capture_output=True,
                    timeout=5,
                )
            
            # Konfiguration lesen (per sudo cat, um memoryview/perms-Fehler zu vermeiden)
            config_lines = []
            if self.wpa_supplicant_file.exists():
                r = subprocess.run(
                    ["sudo", "-S", "cat", str(self.wpa_supplicant_file)],
                    input=_stdin,
                    capture_output=True,
                    timeout=5,
                )
                existing = (r.stdout or b"").decode("utf-8", errors="replace")
                lines = existing.split("\n")
                in_network = False
                skip_network = False
                for line in lines:
                    if "network={" in line:
                        in_network = True
                        skip_network = False
                    if in_network and f'ssid="{ssid}"' in line:
                        skip_network = True
                    if skip_network and line.strip() == "}":
                        in_network = False
                        skip_network = False
                        continue
                    if not skip_network:
                        config_lines.append(line)
            
            # Neues Netzwerk hinzufügen
            config_lines.append("network={")
            config_lines.append(f'    ssid="{ssid}"')
            if security in ["WPA", "WPA2"]:
                config_lines.append(f'    psk="{password}"')
                config_lines.append('    key_mgmt=WPA-PSK')
            else:
                config_lines.append('    key_mgmt=NONE')
            config_lines.append("}")
            
            # Mit sudo schreiben
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".conf") as tmp:
                tmp.write("\n".join(config_lines))
                tmp_path = tmp.name

            subprocess.run(
                ["sudo", "-S", "mv", tmp_path, str(self.wpa_supplicant_file)],
                input=_stdin,
                capture_output=True,
                check=True,
                timeout=5,
            )

            # WiFi neu starten (ermitteltes Interface verwenden)
            iface = self._get_wifi_interface(sudo_password)
            subprocess.run(
                ["sudo", "-S", "wpa_cli", "-i", iface, "reconfigure"],
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            
            return {
                "status": "success",
                "message": "WiFi-Netzwerk hinzugefügt",
                "interface": iface,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler beim Hinzufügen: {str(e)}",
            }

    def get_wifi_status(self, sudo_password: str = "") -> Dict[str, Any]:
        """Aktuell verbundenes WLAN (SSID, Interface, Signal)."""
        iface = self._get_wifi_interface(sudo_password)
        out = ""
        try:
            r = subprocess.run(
                ["wpa_cli", "-i", iface, "status"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = (r.stdout or "") + "\n" + (r.stderr or "")
        except FileNotFoundError:
            pass
        except Exception:
            pass
        connected = False
        ssid = ""
        signal = 0
        for line in out.split("\n"):
            line = line.strip()
            if line.startswith("wpa_state="):
                connected = "COMPLETED" in line
            elif line.startswith("ssid="):
                ssid = line.split("=", 1)[1].strip()
            elif line.startswith("signal=") and "=" in line:
                try:
                    signal = int(line.split("=", 1)[1].strip())
                except Exception:
                    pass
        wifi_enabled = True
        try:
            r = subprocess.run(
                ["rfkill", "list", "wifi"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            txt = (r.stdout or "") + (r.stderr or "")
            t = txt.lower()
            if "soft blocked: yes" in t or "hard blocked: yes" in t:
                wifi_enabled = False
        except Exception:
            pass
        return {
            "status": "success",
            "connected": connected,
            "ssid": ssid or None,
            "interface": iface,
            "signal": signal if connected else None,
            "wifi_enabled": wifi_enabled,
        }

    def wifi_disconnect(self, sudo_password: str = "") -> Dict[str, Any]:
        """Verbindung zum aktuellen WLAN trennen."""
        iface = self._get_wifi_interface(sudo_password)
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            r = subprocess.run(
                ["sudo", "-S", "wpa_cli", "-i", iface, "disconnect"],
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            if r.returncode != 0 and _stdin:
                err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "Trennen fehlgeschlagen"}
            return {"status": "success", "message": "WLAN getrennt", "interface": iface}
        except Exception as e:
            return {"status": "error", "message": f"Fehler beim Trennen: {str(e)}"}

    def wifi_connect(self, ssid: str, sudo_password: str = "") -> Dict[str, Any]:
        """Verbindung zu einem bereits konfigurierten WLAN-Netzwerk herstellen (wpa_cli select_network)."""
        if not (ssid or "").strip():
            return {"status": "error", "message": "SSID erforderlich"}
        iface = self._get_wifi_interface(sudo_password)
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            # wpa_cli list_networks: Ausgabe "network id\tssid\tbssid\tflags"
            r = subprocess.run(
                ["wpa_cli", "-i", iface, "list_networks"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode != 0:
                return {"status": "error", "message": "Netzwerke konnten nicht gelesen werden"}
            network_id = None
            for line in (r.stdout or "").strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1].strip() == ssid.strip():
                    try:
                        network_id = int(parts[0].strip())
                        break
                    except ValueError:
                        continue
            if network_id is None:
                return {"status": "error", "message": f"Netzwerk '{ssid}' nicht in der Konfiguration gefunden"}
            r2 = subprocess.run(
                ["sudo", "-S", "wpa_cli", "-i", iface, "select_network", str(network_id)],
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            if r2.returncode != 0 and _stdin:
                err = (r2.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "Verbinden fehlgeschlagen"}
            subprocess.run(
                ["sudo", "-S", "wpa_cli", "-i", iface, "reconfigure"],
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            return {"status": "success", "message": f"Verbinde mit '{ssid}'", "interface": iface}
        except Exception as e:
            return {"status": "error", "message": f"Fehler beim Verbinden: {str(e)}"}

    def wifi_set_enabled(self, enabled: bool, sudo_password: str = "") -> Dict[str, Any]:
        """WLAN global aktivieren/deaktivieren (rfkill)."""
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            cmd = ["rfkill", "unblock", "wifi"] if enabled else ["rfkill", "block", "wifi"]
            r = subprocess.run(
                ["sudo", "-S"] + cmd,
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            if r.returncode != 0 and _stdin:
                err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "rfkill fehlgeschlagen"}
            return {
                "status": "success",
                "message": f"WLAN {'aktiviert' if enabled else 'deaktiviert'}",
                "enabled": enabled,
            }
        except FileNotFoundError:
            return {"status": "error", "message": "rfkill nicht gefunden"}
        except Exception as e:
            return {"status": "error", "message": f"Fehler: {str(e)}"}

    def get_bluetooth_status(self, sudo_password: str = "") -> Dict[str, Any]:
        """Bluetooth-Status: aktiviert/deaktiviert, verbundene Geräte."""
        bt_enabled = True
        connected_devices = []
        try:
            # Prüfe rfkill-Status
            r = subprocess.run(
                ["rfkill", "list", "bluetooth"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            txt = (r.stdout or "") + (r.stderr or "")
            if "Soft blocked: Yes" in txt.lower() or "Hard blocked: Yes" in txt.lower():
                bt_enabled = False
        except Exception:
            pass
        if not bt_enabled:
            return {
                "status": "success",
                "enabled": False,
                "connected_devices": [],
            }
        # Verbundene Geräte abrufen
        try:
            r = subprocess.run(
                ["bluetoothctl", "--timeout", "2", "devices", "Connected"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in (r.stdout or "").split("\n"):
                line = line.strip()
                if line.startswith("Device "):
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = parts[2]
                        connected_devices.append({"mac": mac, "name": name})
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return {
            "status": "success",
            "enabled": bt_enabled,
            "connected_devices": connected_devices,
        }

    def bluetooth_scan(self, sudo_password: str = "") -> Dict[str, Any]:
        """Bluetooth-Geräte scannen."""
        devices = []
        try:
            # Bluetooth aktivieren falls deaktiviert
            _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
            subprocess.run(
                ["sudo", "-S", "rfkill", "unblock", "bluetooth"],
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            # Bluetooth-Power einschalten
            subprocess.run(
                ["bluetoothctl", "power", "on"],
                capture_output=True,
                timeout=5,
            )
            # Scan starten (10 Sekunden) und danach stoppen
            import time
            proc = subprocess.Popen(
                ["bluetoothctl", "scan", "on"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(10)
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            # Scan stoppen
            subprocess.run(
                ["bluetoothctl", "scan", "off"],
                capture_output=True,
                timeout=5,
            )
            # Geräte abrufen
            r = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # Geräte aus Output parsen
            seen = set()
            for line in (r.stdout or "").split("\n"):
                line = line.strip()
                if line.startswith("Device "):
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3:
                        mac = parts[1]
                        if mac not in seen:
                            seen.add(mac)
                            name = parts[2]
                            devices.append({"mac": mac, "name": name})
        except FileNotFoundError:
            return {"status": "error", "message": "bluetoothctl nicht gefunden"}
        except Exception as e:
            return {"status": "error", "message": f"Scan fehlgeschlagen: {str(e)}"}
        return {"status": "success", "devices": devices}

    def bluetooth_set_enabled(self, enabled: bool, sudo_password: str = "") -> Dict[str, Any]:
        """Bluetooth aktivieren/deaktivieren (rfkill)."""
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            cmd = ["rfkill", "unblock", "bluetooth"] if enabled else ["rfkill", "block", "bluetooth"]
            r = subprocess.run(
                ["sudo", "-S"] + cmd,
                input=_stdin,
                capture_output=True,
                timeout=5,
            )
            if r.returncode != 0 and _stdin:
                err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "rfkill fehlgeschlagen"}
            if enabled:
                # Power einschalten
                subprocess.run(
                    ["bluetoothctl", "power", "on"],
                    capture_output=True,
                    timeout=5,
                )
            return {
                "status": "success",
                "message": f"Bluetooth {'aktiviert' if enabled else 'deaktiviert'}",
                "enabled": enabled,
            }
        except FileNotFoundError:
            return {"status": "error", "message": "rfkill/bluetoothctl nicht gefunden"}
        except Exception as e:
            return {"status": "error", "message": f"Fehler: {str(e)}"}

    def get_ssh_status(self) -> Dict[str, Any]:
        """Prüft SSH-Status"""
        try:
            ssh_enabled = self.ssh_enable_file.exists()
            
            # Prüfe ob SSH-Dienst läuft
            result = subprocess.run(
                ["systemctl", "is-active", "ssh"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ssh_running = result.returncode == 0
            
            return {
                "status": "success",
                "enabled": ssh_enabled,
                "running": ssh_running
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def set_ssh_enabled(self, enabled: bool, sudo_password: str = "") -> Dict[str, Any]:
        """Aktiviert/deaktiviert SSH"""
        try:
            if enabled:
                # SSH aktivieren
                if not self.ssh_enable_file.exists():
                    subprocess.run(
                        ["sudo", "-S", "touch", str(self.ssh_enable_file)],
                        input=sudo_password + '\n' if sudo_password else None,
                        timeout=5
                    )
                # SSH-Dienst starten
                subprocess.run(
                    ["sudo", "-S", "systemctl", "enable", "ssh"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
                subprocess.run(
                    ["sudo", "-S", "systemctl", "start", "ssh"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
            else:
                # SSH deaktivieren
                if self.ssh_enable_file.exists():
                    subprocess.run(
                        ["sudo", "-S", "rm", str(self.ssh_enable_file)],
                        input=sudo_password + '\n' if sudo_password else None,
                        timeout=5
                    )
                subprocess.run(
                    ["sudo", "-S", "systemctl", "stop", "ssh"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
                subprocess.run(
                    ["sudo", "-S", "systemctl", "disable", "ssh"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
            
            return {
                "status": "success",
                "message": f"SSH {'aktiviert' if enabled else 'deaktiviert'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler: {str(e)}"
            }

    def start_ssh_service(self, sudo_password: str = "") -> Dict[str, Any]:
        """SSH-Dienst starten (systemctl start ssh)."""
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            r = subprocess.run(
                ["sudo", "-S", "systemctl", "start", "ssh"],
                input=_stdin,
                capture_output=True,
                timeout=10,
            )
            if r.returncode != 0 and _stdin:
                err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "SSH starten fehlgeschlagen"}
            return {"status": "success", "message": "SSH gestartet"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_vnc_status(self) -> Dict[str, Any]:
        """Prüft VNC-Status"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "vncserver-x11-serviced"],
                capture_output=True,
                text=True,
                timeout=5
            )
            vnc_running = result.returncode == 0
            
            return {
                "status": "success",
                "running": vnc_running
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def set_vnc_enabled(self, enabled: bool, password: str = "", sudo_password: str = "") -> Dict[str, Any]:
        """Aktiviert/deaktiviert VNC"""
        try:
            if enabled:
                # VNC aktivieren
                subprocess.run(
                    ["sudo", "-S", "systemctl", "enable", "vncserver-x11-serviced"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
                subprocess.run(
                    ["sudo", "-S", "systemctl", "start", "vncserver-x11-serviced"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
                if password:
                    # VNC-Passwort setzen
                    subprocess.run(
                        ["sudo", "-S", "vncpasswd", "-service"],
                        input=f"{password}\n{password}\n" + sudo_password + '\n' if sudo_password else f"{password}\n{password}\n",
                        timeout=5
                    )
            else:
                subprocess.run(
                    ["sudo", "-S", "systemctl", "stop", "vncserver-x11-serviced"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
                subprocess.run(
                    ["sudo", "-S", "systemctl", "disable", "vncserver-x11-serviced"],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
            
            return {
                "status": "success",
                "message": f"VNC {'aktiviert' if enabled else 'deaktiviert'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler: {str(e)}"
            }

    def start_vnc_service(self, sudo_password: str = "") -> Dict[str, Any]:
        """VNC-Dienst starten (systemctl start vncserver-x11-serviced)."""
        _stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
        try:
            r = subprocess.run(
                ["sudo", "-S", "systemctl", "start", "vncserver-x11-serviced"],
                input=_stdin,
                capture_output=True,
                timeout=10,
            )
            if r.returncode != 0 and _stdin:
                err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
                return {"status": "error", "message": err or "VNC starten fehlgeschlagen"}
            return {"status": "success", "message": "VNC gestartet"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_keyboard_layout(self) -> Dict[str, Any]:
        """Liest Tastatur-Layout"""
        try:
            layout = "de"
            variant = "de"
            options = ""
            
            if self.x11_keyboard_file.exists():
                with open(self.x11_keyboard_file, 'r') as f:
                    for line in f:
                        if line.startswith('XKBLAYOUT='):
                            layout = line.split('=', 1)[1].strip().strip('"')
                        elif line.startswith('XKBVARIANT='):
                            variant = line.split('=', 1)[1].strip().strip('"')
                        elif line.startswith('XKBOPTIONS='):
                            options = line.split('=', 1)[1].strip().strip('"')
            
            return {
                "status": "success",
                "layout": layout,
                "variant": variant,
                "options": options
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def set_keyboard_layout(self, layout: str, variant: str = "", options: str = "", sudo_password: str = "") -> Dict[str, Any]:
        """Setzt Tastatur-Layout"""
        try:
            lines = []
            if self.x11_keyboard_file.exists():
                with open(self.x11_keyboard_file, 'r') as f:
                    lines = f.readlines()
            
            # Aktualisiere oder füge hinzu
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith('XKBLAYOUT='):
                    new_lines.append(f'XKBLAYOUT="{layout}"\n')
                    updated = True
                elif line.startswith('XKBVARIANT='):
                    if variant:
                        new_lines.append(f'XKBVARIANT="{variant}"\n')
                        updated = True
                    else:
                        continue  # Entferne Variante
                elif line.startswith('XKBOPTIONS='):
                    if options:
                        new_lines.append(f'XKBOPTIONS="{options}"\n')
                        updated = True
                    else:
                        continue  # Entferne Options
                else:
                    new_lines.append(line)
            
            if not updated:
                new_lines.append(f'XKBLAYOUT="{layout}"\n')
                if variant:
                    new_lines.append(f'XKBVARIANT="{variant}"\n')
                if options:
                    new_lines.append(f'XKBOPTIONS="{options}"\n')
            
            # Mit sudo schreiben
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                tmp.writelines(new_lines)
                tmp_path = tmp.name
            
            subprocess.run(
                ["sudo", "-S", "mv", tmp_path, str(self.x11_keyboard_file)],
                input=sudo_password + '\n' if sudo_password else None,
                check=True,
                timeout=5
            )
            
            # Tastatur neu laden
            subprocess.run(
                ["sudo", "-S", "setupcon", "--save"],
                input=sudo_password + '\n' if sudo_password else None,
                timeout=5
            )
            
            return {
                "status": "success",
                "message": "Tastatur-Layout gesetzt"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler: {str(e)}"
            }
    
    def get_locale(self) -> Dict[str, Any]:
        """Liest Locale-Einstellungen"""
        try:
            locale = "de_DE.UTF-8"
            timezone = "Europe/Berlin"
            
            if self.locale_conf_file.exists():
                with open(self.locale_conf_file, 'r') as f:
                    for line in f:
                        if line.startswith('LANG='):
                            locale = line.split('=', 1)[1].strip().strip('"')
            
            # Timezone lesen
            try:
                result = subprocess.run(
                    ["timedatectl", "show", "--property=TimeZone", "--value"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    timezone = result.stdout.strip()
            except:
                pass
            
            return {
                "status": "success",
                "locale": locale,
                "timezone": timezone
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def set_locale(self, locale: str, timezone: str = "", sudo_password: str = "") -> Dict[str, Any]:
        """Setzt Locale und Timezone"""
        try:
            # Locale setzen
            if self.locale_conf_file.exists():
                with open(self.locale_conf_file, 'w') as f:
                    f.write(f'LANG="{locale}"\n')
                    f.write(f'LANGUAGE="{locale}"\n')
            
            # Locale generieren
            subprocess.run(
                ["sudo", "-S", "locale-gen", locale],
                input=sudo_password + '\n' if sudo_password else None,
                timeout=10
            )
            
            # Timezone setzen
            if timezone:
                subprocess.run(
                    ["sudo", "-S", "timedatectl", "set-timezone", timezone],
                    input=sudo_password + '\n' if sudo_password else None,
                    timeout=5
                )
            
            return {
                "status": "success",
                "message": "Locale gesetzt"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler: {str(e)}"
            }
    
    def get_boot_target(self) -> Dict[str, Any]:
        """Liest das aktuelle Boot-Ziel (Desktop vs. Kommandozeile). Kein sudo nötig."""
        try:
            r = subprocess.run(
                ["systemctl", "get-default"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            raw = (r.stdout or "").strip() if r.returncode == 0 else ""
            target = "graphical" if "graphical" in raw else ("multi-user" if "multi-user" in raw else raw or "unknown")
            label = "Desktop" if target == "graphical" else ("Kommandozeile" if target == "multi-user" else raw or "Unbekannt")
            return {
                "status": "success",
                "target": target,
                "raw": raw,
                "label": label,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "target": None, "label": None}

    def set_boot_target(self, target: str, sudo_password: str = "") -> Dict[str, Any]:
        """Setzt das Boot-Ziel: graphical (Desktop) oder multi-user (Kommandozeile)."""
        t = (target or "").strip().lower()
        if t in ("graphical", "graphical.target"):
            unit = "graphical.target"
        elif t in ("multi-user", "multi-user.target", "console", "cli"):
            unit = "multi-user.target"
        else:
            return {"status": "error", "message": "Ungültiges Ziel. Erlaubt: graphical (Desktop) oder multi-user (Kommandozeile)."}
        try:
            cmd = ["sudo", "-S", "systemctl", "set-default", unit]
            stdin = (sudo_password + "\n").encode("utf-8") if sudo_password else None
            r = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                timeout=10,
            )
            if r.returncode != 0:
                err = (r.stderr or b"").decode("utf-8", errors="ignore").strip() or "Unbekannter Fehler"
                return {"status": "error", "message": f"systemctl set-default fehlgeschlagen: {err}"}
            return {
                "status": "success",
                "message": "Boot-Ziel gespeichert. Wirkt nach dem nächsten Neustart.",
                "target": "graphical" if unit == "graphical.target" else "multi-user",
                "label": "Desktop" if unit == "graphical.target" else "Kommandozeile",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_desktop_settings(self) -> Dict[str, Any]:
        """Liest Desktop-Einstellungen"""
        try:
            # Versuche dconf oder gsettings zu verwenden
            settings = {
                "wallpaper": "",
                "theme": "",
                "icon_theme": "",
                "cursor_theme": "",
                "font_size": 10,
                "auto_login": False
            }
            
            try:
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    settings["wallpaper"] = result.stdout.strip().strip("'\"")
            except:
                pass
            
            return {
                "status": "success",
                "settings": settings
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _parse_xrandr(self, out: str) -> List[Dict[str, Any]]:
        """Parst xrandr-Ausgabe: connected Outputs, aktuelle Auflösung/Refresh, Modi."""
        outputs: List[Dict[str, Any]] = []
        current_output: Optional[Dict[str, Any]] = None
        for line in (out or "").splitlines():
            line = line.rstrip()
            if not line:
                continue
            if line.startswith(" ") or line.startswith("\t"):
                # Modus-Zeile: "   1920x1080     60.00*+  50.00    59.94"
                if current_output is None:
                    continue
                parts = line.split()
                if not parts or "x" not in parts[0] or not parts[0][0].isdigit():
                    continue
                mode = parts[0]
                rates: List[float] = []
                current_rate: Optional[float] = None
                for i in range(1, len(parts)):
                    s = parts[i].strip().rstrip("*+")
                    try:
                        r = float(s)
                        rates.append(r)
                        if "*" in parts[i]:
                            current_rate = r
                    except ValueError:
                        pass
                if not rates:
                    continue
                m = {"mode": mode, "rates": rates, "current": current_rate}
                if "modes" not in current_output:
                    current_output["modes"] = []
                current_output["modes"].append(m)
                if current_rate is not None and "refresh_rate" not in current_output:
                    current_output["refresh_rate"] = current_rate
                continue
            # Output-Zeile
            if current_output and current_output.get("connected"):
                outputs.append(current_output)
            current_output = None
            if " connected" not in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0]
            res = None
            for p in parts[2:]:
                if "x" in p and p[0].isdigit():
                    res = p.split("+")[0].split("@")[0]
                    break
            current_output = {
                "name": name,
                "connected": True,
                "resolution": res or "1920x1080",
                "refresh_rate": 60.0,
                "rotation": "normal",
                "modes": [],
            }
        if current_output and current_output.get("connected"):
            outputs.append(current_output)
        return outputs

    def _display_env(self) -> Dict[str, str]:
        """Umgebung für xrandr: DISPLAY setzen falls nicht gesetzt (Backend oft ohne X)."""
        env = dict(os.environ)
        if not env.get("DISPLAY"):
            env["DISPLAY"] = ":0"
        return env

    def _parse_xrandr_verbose_rotation(self, out: str) -> Dict[str, str]:
        """Extrahiert aus 'xrandr --query --verbose' die Rotation pro Output."""
        rot: Dict[str, str] = {}
        cur = None
        for line in (out or "").splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                if "rotation:" in line and cur:
                    try:
                        v = line.split("rotation:")[1].strip().lower()
                        if v in ("normal", "left", "right", "inverted"):
                            rot[cur] = v
                    except IndexError:
                        pass
            else:
                parts = line.split()
                if parts and "connected" in line:
                    cur = parts[0]
                else:
                    cur = None
        return rot

    def _display_fallback_output(self) -> List[Dict[str, Any]]:
        """Fallback-Output wenn xrandr nicht erreichbar."""
        return [{
            "name": "HDMI-1",
            "connected": True,
            "resolution": "1920x1080",
            "refresh_rate": 60.0,
            "rotation": "normal",
            "modes": [{"mode": "1920x1080", "rates": [60.0, 50.0], "current": 60.0}],
        }]

    def get_display_settings(self) -> Dict[str, Any]:
        """Liest Display-Einstellungen (xrandr). Kein sudo. Bei Fehler Fallback."""
        fallback = False
        outputs: List[Dict[str, Any]] = []
        brightness: Optional[Dict[str, Any]] = None
        env = self._display_env()
        try:
            try:
                r = subprocess.run(
                    ["xrandr", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env=env,
                )
                if r.returncode == 0 and (r.stdout or "").strip():
                    outputs = self._parse_xrandr(r.stdout)
            except Exception:
                pass
            if not outputs:
                fallback = True
                outputs = self._display_fallback_output()
            else:
                try:
                    rv = subprocess.run(
                        ["xrandr", "--query", "--verbose"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        env=env,
                    )
                    if rv.returncode == 0 and (rv.stdout or "").strip():
                        rot_map = self._parse_xrandr_verbose_rotation(rv.stdout)
                        for o in outputs:
                            o["rotation"] = rot_map.get(o["name"], "normal")
                except Exception:
                    pass
            try:
                bl = list(Path("/sys/class/backlight").glob("*/brightness"))
                bl_max = list(Path("/sys/class/backlight").glob("*/max_brightness"))
                if bl and bl_max:
                    mx = int(bl_max[0].read_text().strip())
                    cur = int(bl[0].read_text().strip())
                    brightness = {"current": cur, "max": mx, "path": str(bl[0])}
            except Exception:
                pass
            return {
                "status": "success",
                "outputs": outputs,
                "brightness": brightness,
                "fallback": fallback,
            }
        except Exception as e:
            return {
                "status": "success",
                "outputs": self._display_fallback_output(),
                "brightness": None,
                "fallback": True,
                "message": str(e),
            }

    def set_display_settings(
        self,
        output: str,
        mode: str,
        rate: Optional[float] = None,
        rotation: Optional[str] = None,
        sudo_password: str = "",
    ) -> Dict[str, Any]:
        """Setzt Display via xrandr (Auflösung, Wiederholrate, Rotation). Kein sudo nötig."""
        out = (output or "").strip() or "HDMI-1"
        m = (mode or "").strip() or "1920x1080"
        rot = (rotation or "").strip().lower() or "normal"
        if rot not in ("normal", "left", "right", "inverted"):
            rot = "normal"
        cmd = ["xrandr", "--output", out, "--mode", m]
        if rate is not None and rate > 0:
            cmd += ["--rate", str(round(rate, 2))]
        cmd += ["--rotate", rot]
        env = self._display_env()
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=env)
            if r.returncode != 0:
                err = (r.stderr or "").strip() or "Unbekannter Fehler"
                return {"status": "error", "message": f"xrandr fehlgeschlagen: {err}"}
            return {
                "status": "success",
                "message": "Display-Einstellungen übernommen.",
                "output": out,
                "mode": m,
                "rate": rate,
                "rotation": rot,
            }
        except FileNotFoundError:
            return {"status": "error", "message": "xrandr nicht gefunden. Läuft eine grafische Oberfläche (X/Wayland)?"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_printers(self, sudo_password: str = "") -> Dict[str, Any]:
        """Listet Drucker auf (lpstat -p). Bei Locale 'de' z.B. 'Drucker NAME ...'; sonst 'printer NAME ...'."""
        printers = []
        try:
            result = subprocess.run(
                ["lpstat", "-p"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in (result.stdout or "").strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                # "printer NAME ..." (en) oder "Drucker NAME ..." (de)
                if line.lower().startswith("printer ") or line.startswith("Drucker "):
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[1]
                        low = line.lower()
                        if "idle" in low or "leerlauf" in low:
                            status = "idle"
                        elif "printing" in low or "druckt" in low:
                            status = "printing"
                        elif "disabled" in low or "deaktiviert" in low:
                            status = "disabled"
                        else:
                            status = "unknown"
                        printers.append({"name": name, "status": status})
            return {"status": "success", "printers": printers}
        except FileNotFoundError:
            return {"status": "error", "message": "lpstat nicht gefunden. Ist CUPS installiert? (apt install cups)"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "lpstat hat zu lange gedauert."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _check_sane_installed(self) -> Dict[str, Any]:
        """Prüft ob SANE und zugehörige Programme installiert sind."""
        out: Dict[str, Any] = {
            "scanimage": False,
            "scanimage_path": None,
            "sane_find_scanner": False,
            "sane_find_scanner_path": None,
            "packages": {},
        }
        # which scanimage / sane-find-scanner
        for cmd, key, path_key in [
            ("scanimage", "scanimage", "scanimage_path"),
            ("sane-find-scanner", "sane_find_scanner", "sane_find_scanner_path"),
        ]:
            try:
                r = subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if r.returncode == 0 and (r.stdout or "").strip():
                    out[key] = True
                    out[path_key] = (r.stdout or "").strip().splitlines()[0].strip()
                else:
                    out[path_key] = None
            except Exception:
                out[path_key] = None
        # dpkg -l sane-utils sane-airscan (sane/sane-backends sind keine Debian-Pakete)
        try:
            r = subprocess.run(
                ["dpkg", "-l", "sane-utils", "sane-airscan"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in (r.stdout or "").splitlines():
                if not line.startswith("ii "):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    pkg = parts[1].split(":")[0]
                    out["packages"][pkg] = True
            for p in ("sane-utils", "sane-airscan"):
                if p not in out["packages"]:
                    out["packages"][p] = False
        except Exception:
            out["packages"] = {"sane-utils": False, "sane-airscan": False}
        return out

    def get_scanners(self, sudo_password: str = "") -> Dict[str, Any]:
        """Listet SANE-Scanner auf (scanimage -L). Enthält sane_check mit Installationsstatus."""
        sane_check = self._check_sane_installed()
        scanners = []
        try:
            # Netzwerk-Scanner (eSCL/airscan) können 20+ s brauchen
            result = subprocess.run(
                ["scanimage", "-L"],
                capture_output=True,
                text=True,
                timeout=45,
            )
            # Zeilen wie: device `escl:https://...' is a ESCL Kyocera ECOSYS M5526cdw platen,adf scanner
            # Bei eSCL/airscan oft "404 Page Not Found" am Zeilenanfang vor device – daher search, nicht match
            pattern = re.compile(r"device\s+`([^']+)'\s+is\s+a\s+(.+)")
            for line in (result.stdout or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                m = pattern.search(line)
                if m:
                    device = m.group(1).strip()
                    desc = m.group(2).strip()
                    name = re.sub(r"\s+platen.*$", "", desc, flags=re.I).strip() or desc
                    scanners.append({"name": name, "device": device})
            return {"status": "success", "scanners": scanners, "sane_check": sane_check}
        except FileNotFoundError:
            return {
                "status": "error",
                "message": "scanimage nicht gefunden. Installieren: apt update && apt install sane-utils (ggf. sane-airscan für Netzwerk-Scanner).",
                "scanners": [],
                "sane_check": sane_check,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "scanimage hat zu lange gedauert (Timeout). Netzwerk-Scanner prüfen.",
                "scanners": [],
                "sane_check": sane_check,
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "scanners": [], "sane_check": sane_check}

    def _cpu_governor_paths(self) -> List[Path]:
        """Liefert cpufreq-Pfade für alle CPUs (scaling_governor, scaling_available_governors)."""
        base = Path("/sys/devices/system/cpu")
        paths = []
        for p in sorted(base.glob("cpu[0-9]*")):
            g = p / "cpufreq" / "scaling_governor"
            a = p / "cpufreq" / "scaling_available_governors"
            if g.exists() and a.exists():
                paths.append((g, a))
        return paths

    def get_performance(self, sudo_password: str = "") -> Dict[str, Any]:
        """Liest CPU-Governor, GPU-Memory/Overclocking (config.txt) und Swap."""
        out: Dict[str, Any] = {
            "governor": None,
            "governors": [],
            "gpu_mem": None,
            "arm_freq": None,
            "over_voltage": None,
            "force_turbo": None,
            "swap_total_mb": 0,
            "swap_used_mb": 0,
            "swap_size_mb": None,
            "swap_editable": False,
        }
        # CPU Governor
        try:
            paths = self._cpu_governor_paths()
            if paths:
                gov_path, av_path = paths[0]
                out["governor"] = gov_path.read_text().strip()
                out["governors"] = [s.strip() for s in av_path.read_text().split() if s.strip()]
        except Exception:
            pass
        # config.txt (gpu_mem, overclocking) via Raspberry-Pi-Modul
        try:
            from modules.raspberry_pi_config import RaspberryPiConfigModule
            pi = RaspberryPiConfigModule()
            r = pi.read_config(sudo_password=sudo_password)
            if r.get("status") == "success" and isinstance(r.get("config"), dict):
                c = r["config"]
                out["gpu_mem"] = c.get("gpu_mem")
                out["arm_freq"] = c.get("arm_freq")
                out["over_voltage"] = c.get("over_voltage")
                out["force_turbo"] = c.get("force_turbo")
        except Exception:
            pass
        # Swap: swapon + ggf. dphys-swapfile
        try:
            r = subprocess.run(
                ["swapon", "--show=NAME,SIZE,USED", "--noheadings"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            total = 0
            used = 0
            for line in (r.stdout or "").strip().splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        total += int(parts[1])
                        used += int(parts[2])
                    except ValueError:
                        pass
            out["swap_total_mb"] = total // 1024
            out["swap_used_mb"] = used // 1024
        except Exception:
            pass
        dp = Path("/etc/dphys-swapfile")
        if dp.exists():
            try:
                raw = dp.read_text()
                for line in raw.splitlines():
                    line = line.strip()
                    if line.startswith("CONF_SWAPSIZE="):
                        val = line.split("=", 1)[1].strip()
                        try:
                            out["swap_size_mb"] = int(val)
                        except ValueError:
                            out["swap_size_mb"] = None
                        break
                out["swap_editable"] = True
            except Exception:
                pass
        return {"status": "success", **out}

    def set_performance(
        self,
        sudo_password: str,
        governor: Optional[str] = None,
        gpu_mem: Optional[str] = None,
        arm_freq: Optional[str] = None,
        over_voltage: Optional[str] = None,
        force_turbo: Optional[bool] = None,
        swap_size_mb: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Setzt Governor, config-Optionen und/oder Swap-Größe. Config/Swap erfordern Neustart."""
        messages: List[str] = []
        # CPU Governor (sofort wirksam)
        if governor is not None:
            paths = self._cpu_governor_paths()
            if not paths:
                return {"status": "error", "message": "cpufreq/Governor nicht verfügbar."}
            gov_paths = [str(p[0]) for p in paths]
            try:
                cmd = " && ".join(f"echo {shlex.quote(governor)} > {shlex.quote(p)}" for p in gov_paths)
                r = subprocess.run(
                    ["sudo", "-S", "sh", "-c", cmd],
                    input=(sudo_password + "\n").encode(),
                    capture_output=True,
                    timeout=10,
                )
                if r.returncode != 0:
                    err = (r.stderr or r.stdout or b"").decode("utf-8", errors="ignore").strip() or "Unbekannter Fehler"
                    return {"status": "error", "message": f"Governor setzen fehlgeschlagen: {err}"}
                messages.append("CPU-Governor gesetzt.")
            except Exception as e:
                return {"status": "error", "message": f"Governor setzen fehlgeschlagen: {e}"}
        # config.txt (gpu_mem, overclocking)
        config_updates = {}
        if gpu_mem is not None:
            config_updates["gpu_mem"] = str(gpu_mem)
        if arm_freq is not None:
            config_updates["arm_freq"] = str(arm_freq)
        if over_voltage is not None:
            config_updates["over_voltage"] = str(over_voltage)
        if force_turbo is not None:
            config_updates["force_turbo"] = 1 if force_turbo else 0
        if config_updates:
            try:
                from modules.raspberry_pi_config import RaspberryPiConfigModule
                pi = RaspberryPiConfigModule()
                r = pi.read_config(sudo_password=sudo_password)
                if r.get("status") != "success" or not isinstance(r.get("config"), dict):
                    return {"status": "error", "message": r.get("message", "config.txt lesen fehlgeschlagen.")}
                merged = {**r["config"], **config_updates}
                w = pi.write_config(merged, sudo_password)
                if w.get("status") != "success":
                    return {"status": "error", "message": w.get("message", "config.txt schreiben fehlgeschlagen.")}
                messages.append("Konfiguration (GPU/Overclocking) gespeichert. Neustart erforderlich.")
            except Exception as e:
                return {"status": "error", "message": f"Config schreiben fehlgeschlagen: {e}"}
        # Swap (dphys-swapfile)
        if swap_size_mb is not None:
            dp = Path("/etc/dphys-swapfile")
            if not dp.exists():
                return {"status": "error", "message": "dphys-swapfile nicht gefunden. Swap-Größe kann hier nicht geändert werden."}
            try:
                raw = dp.read_text()
                lines = []
                done = False
                for line in raw.splitlines():
                    if line.strip().startswith("CONF_SWAPSIZE="):
                        lines.append(f"CONF_SWAPSIZE={swap_size_mb}\n")
                        done = True
                    else:
                        lines.append(line.rstrip("\n") + "\n")
                if not done:
                    lines.append(f"CONF_SWAPSIZE={swap_size_mb}\n")
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", suffix=".dphys", delete=False) as f:
                    f.write("".join(lines))
                    tmp = Path(f.name)
                try:
                    subprocess.run(
                        ["sudo", "-S", "cp", str(tmp), str(dp)],
                        input=(sudo_password + "\n").encode(),
                        capture_output=True,
                        timeout=5,
                        check=True,
                    )
                finally:
                    tmp.unlink(missing_ok=True)
                for cmd in [["dphys-swapfile", "swapoff"], ["dphys-swapfile", "setup"], ["dphys-swapfile", "swapon"]]:
                    subprocess.run(
                        ["sudo", "-S"] + cmd,
                        input=(sudo_password + "\n").encode(),
                        capture_output=True,
                        timeout=60 if cmd[1] == "setup" else 15,
                    )
                messages.append("Swap-Größe angepasst.")
            except Exception as e:
                return {"status": "error", "message": f"Swap anpassen fehlgeschlagen: {e}"}
        return {"status": "success", "message": " ".join(messages) if messages else "Keine Änderungen."}
