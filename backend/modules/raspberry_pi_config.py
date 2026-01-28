"""
Raspberry Pi Konfigurationsmodul
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import shlex
import json
import re
import psutil


class RaspberryPiConfigModule:
    """Raspberry Pi Konfiguration verwalten"""
    
    def __init__(self):
        self.config_file = Path("/boot/firmware/config.txt")  # Raspberry Pi OS (Debian)
        self.config_file_legacy = Path("/boot/config.txt")  # Legacy
        self.cmdline_file = Path("/boot/firmware/cmdline.txt")
        self.cmdline_file_legacy = Path("/boot/cmdline.txt")
        
        # Konfigurationsoptionen mit Beschreibungen und Bereichszuordnung
        self.config_options = {
            "gpu_mem": {
                "name": "GPU Speicher",
                "description": "Speicher für die GPU reservieren (16-512 MB). Mehr GPU-Speicher ermöglicht bessere Video-Performance, reduziert aber den verfügbaren RAM. Hinweis: 256 MB oder mehr kann bei einigen Setups zu rosa/magentafarbenen Bildschirm-Artefakten führen (z. B. beim Start von Cursor). Dann auf 64–128 MB zurücksetzen.",
                "default": "64",
                "type": "int",
                "range": (16, 512),
                "unit": "MB",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: config.txt"
            },
            "gpu_mem_256": {
                "name": "GPU Speicher (256MB Pi)",
                "description": "GPU-Speicher für Raspberry Pi mit 256MB RAM.",
                "default": "64",
                "type": "int",
                "range": (16, 256),
                "unit": "MB",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: config.txt"
            },
            "gpu_mem_512": {
                "name": "GPU Speicher (512MB Pi)",
                "description": "GPU-Speicher für Raspberry Pi mit 512MB RAM.",
                "default": "128",
                "type": "int",
                "range": (16, 512),
                "unit": "MB",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: config.txt"
            },
            "arm_freq": {
                "name": "CPU Frequenz",
                "description": "CPU-Taktfrequenz in MHz. Erhöhung kann Performance verbessern, benötigt aber mehr Strom und erzeugt mehr Wärme.",
                "default": "auto",
                "type": "str",
                "options": ["auto", "600", "700", "800", "900", "1000", "1100", "1200", "1300", "1400", "1500"],
                "category": "overclocking",
                "source": "Raspberry Pi Documentation: config.txt - Overclocking"
            },
            "over_voltage": {
                "name": "Spannungserhöhung",
                "description": "Erhöht die Spannung für höhere CPU-Taktraten. Vorsicht: Kann Hardware beschädigen! Nur für erfahrene Benutzer.",
                "default": "0",
                "type": "int",
                "range": (-16, 8),
                "unit": "mV",
                "category": "overclocking",
                "source": "Raspberry Pi Documentation: config.txt - Overclocking"
            },
            "force_turbo": {
                "name": "Turbo-Modus erzwingen",
                "description": "Erzwingt maximale CPU-Taktfrequenz. Erhöht Stromverbrauch und Wärmeentwicklung erheblich.",
                "default": "0",
                "type": "bool",
                "category": "overclocking",
                "source": "Raspberry Pi Documentation: config.txt - Overclocking"
            },
            "disable_overscan": {
                "name": "Overscan deaktivieren",
                "description": "Deaktiviert automatische Bildschirmanpassung. Aktivieren, wenn schwarze Ränder am Bildschirmrand erscheinen.",
                "default": "0",
                "type": "bool",
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Display"
            },
            "hdmi_group": {
                "name": "HDMI Gruppe",
                "description": "HDMI-Standardgruppe: 0=Auto, 1=CEA (TV), 2=DMT (Monitor).",
                "default": "0",
                "type": "int",
                "options": [0, 1, 2],
                "category": "hdmi",
                "source": "Raspberry Pi Documentation: config.txt - HDMI"
            },
            "hdmi_mode": {
                "name": "HDMI Modus",
                "description": "HDMI-Auflösung und Bildwiederholrate. Abhängig von hdmi_group.",
                "default": "0",
                "type": "int",
                "range": (0, 87),
                "category": "hdmi",
                "source": "Raspberry Pi Documentation: config.txt - HDMI"
            },
            "hdmi_force_hotplug": {
                "name": "HDMI Hotplug erzwingen",
                "description": "Erzwingt HDMI-Ausgabe auch wenn kein Monitor erkannt wird. Nützlich für Headless-Setup.",
                "default": "0",
                "type": "bool",
                "category": "hdmi",
                "source": "Raspberry Pi Documentation: config.txt - HDMI"
            },
            "hdmi_ignore_edid": {
                "name": "HDMI EDID ignorieren",
                "description": "Ignoriert Monitor-Informationen. Kann helfen bei Kompatibilitätsproblemen.",
                "default": "0",
                "type": "bool",
                "category": "hdmi",
                "source": "Raspberry Pi Documentation: config.txt - HDMI"
            },
            "hdmi_drive": {
                "name": "HDMI Treiber",
                "description": "HDMI-Treibermodus: 1=DVI (kein Audio), 2=HDMI (mit Audio).",
                "default": "2",
                "type": "int",
                "options": [1, 2],
                "category": "hdmi",
                "source": "Raspberry Pi Documentation: config.txt - HDMI"
            },
            "sdtv_mode": {
                "name": "SDTV Modus",
                "description": "Composite-Video-Modus: 0=NTSC, 1=NTSC-J, 2=PAL, 3=PAL-M, 16=NTSC 4:3, 18=PAL 4:3.",
                "default": "2",
                "type": "int",
                "options": [0, 1, 2, 3, 16, 18],
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Composite Video"
            },
            "sdtv_aspect": {
                "name": "SDTV Seitenverhältnis",
                "description": "Composite-Video-Seitenverhältnis: 1=4:3, 2=14:9, 3=16:9.",
                "default": "1",
                "type": "int",
                "options": [1, 2, 3],
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Composite Video"
            },
            "display_rotate": {
                "name": "Bildschirmrotation",
                "description": "Rotiert die Bildschirmausgabe: 0=Normal, 1=90°, 2=180°, 3=270°.",
                "default": "0",
                "type": "int",
                "options": [0, 1, 2, 3],
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Display"
            },
            "framebuffer_width": {
                "name": "Framebuffer Breite",
                "description": "Framebuffer-Breite in Pixeln. Wird automatisch gesetzt, wenn nicht angegeben.",
                "default": "auto",
                "type": "int",
                "range": (1, 7680),
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Framebuffer"
            },
            "framebuffer_height": {
                "name": "Framebuffer Höhe",
                "description": "Framebuffer-Höhe in Pixeln. Wird automatisch gesetzt, wenn nicht angegeben.",
                "default": "auto",
                "type": "int",
                "range": (1, 4320),
                "category": "display",
                "source": "Raspberry Pi Documentation: config.txt - Framebuffer"
            },
            "enable_uart": {
                "name": "UART aktivieren",
                "description": "Aktiviert die serielle Schnittstelle (UART). Wichtig für GPIO-Kommunikation und Debugging.",
                "default": "0",
                "type": "bool",
                "category": "gpio",
                "source": "Raspberry Pi Documentation: config.txt - UART"
            },
            "uart_2ndstage": {
                "name": "UART 2nd Stage",
                "description": "Aktiviert UART bereits im Bootloader. Für erweiterte Debugging-Zwecke.",
                "default": "0",
                "type": "bool",
                "category": "gpio",
                "source": "Raspberry Pi Documentation: config.txt - UART"
            },
            "enable_camera": {
                "name": "Kamera aktivieren",
                "description": "Aktiviert die Raspberry Pi Kamera (CSI). Erforderlich für Raspberry Pi Kamera-Module.",
                "default": "0",
                "type": "bool",
                "category": "camera",
                "source": "Raspberry Pi Documentation: config.txt - Camera"
            },
            "start_x": {
                "name": "GPU Start",
                "description": "Startet die GPU beim Booten. Erforderlich für Kamera und Video-Beschleunigung.",
                "default": "0",
                "type": "bool",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: config.txt - GPU"
            },
            "disable_camera_led": {
                "name": "Kamera-LED deaktivieren",
                "description": "Deaktiviert die rote LED der Kamera beim Aufnehmen. Nützlich für diskrete Aufnahmen.",
                "default": "0",
                "type": "bool",
                "category": "camera",
                "source": "Raspberry Pi Documentation: config.txt - Camera"
            },
            "dtparam=i2c_arm": {
                "name": "I2C aktivieren",
                "description": "Aktiviert I2C-Bus für Sensoren und Displays. Wird häufig für Sensoren benötigt.",
                "default": "off",
                "type": "bool",
                "category": "gpio",
                "source": "Raspberry Pi Documentation: Device Tree Parameters"
            },
            "dtparam=i2s": {
                "name": "I2S aktivieren",
                "description": "Aktiviert I2S-Bus für Audio-Hardware. Für High-Quality-Audio-Interfaces.",
                "default": "off",
                "type": "bool",
                "category": "gpio",
                "source": "Raspberry Pi Documentation: Device Tree Parameters"
            },
            "dtparam=spi": {
                "name": "SPI aktivieren",
                "description": "Aktiviert SPI-Bus für Displays und Sensoren. Wird für viele LCD-Displays benötigt.",
                "default": "off",
                "type": "bool",
                "category": "gpio",
                "source": "Raspberry Pi Documentation: Device Tree Parameters"
            },
            "dtoverlay=vc4-kms-v3d": {
                "name": "KMS Video-Treiber",
                "description": "Aktiviert den modernen KMS-Video-Treiber. Verbessert Grafik-Performance und Multi-Monitor-Support.",
                "default": "off",
                "type": "bool",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: Device Tree Overlays"
            },
            "dtoverlay=vc4-fkms-v3d": {
                "name": "FKMS Video-Treiber",
                "description": "Aktiviert den Fake-KMS-Video-Treiber. Ältere Alternative zu KMS mit weniger Features.",
                "default": "off",
                "type": "bool",
                "category": "gpu",
                "source": "Raspberry Pi Documentation: Device Tree Overlays"
            },
            "dtoverlay=disable-wifi": {
                "name": "WiFi deaktivieren",
                "description": "Deaktiviert WiFi-Hardware. Spart Strom und kann bei Funkstörungen helfen.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays"
            },
            "dtoverlay=disable-bt": {
                "name": "Bluetooth deaktivieren",
                "description": "Deaktiviert Bluetooth-Hardware. Spart Strom.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays"
            },
            "dtoverlay=miniuart-bt": {
                "name": "Mini-UART für Bluetooth",
                "description": "Verwendet Mini-UART für Bluetooth, gibt Haupt-UART frei.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays"
            },
            "dtoverlay=pi3-disable-wifi": {
                "name": "WiFi deaktivieren (Pi 3)",
                "description": "Deaktiviert WiFi auf Raspberry Pi 3.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays - Pi 3"
            },
            "dtoverlay=pi3-disable-bt": {
                "name": "Bluetooth deaktivieren (Pi 3)",
                "description": "Deaktiviert Bluetooth auf Raspberry Pi 3.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays - Pi 3"
            },
            "dtoverlay=pi3-miniuart-bt": {
                "name": "Mini-UART für Bluetooth (Pi 3)",
                "description": "Verwendet Mini-UART für Bluetooth auf Raspberry Pi 3.",
                "default": "off",
                "type": "bool",
                "category": "wireless",
                "source": "Raspberry Pi Documentation: Device Tree Overlays - Pi 3"
            },
        }
    
    def get_config_file(self) -> Path:
        """Ermittelt die richtige config.txt Datei"""
        if self.config_file.exists():
            return self.config_file
        elif self.config_file_legacy.exists():
            return self.config_file_legacy
        else:
            return self.config_file  # Default
    
    def read_config(self, sudo_password: str = "") -> Dict[str, Any]:
        """Liest die aktuelle Konfiguration"""
        config_file = self.get_config_file()
        
        if not config_file.exists():
            return {
                "status": "error",
                "message": f"config.txt nicht gefunden: {config_file}",
                "config": {}
            }
        
        try:
            config = {}
            # Versuche mit sudo zu lesen, falls normale Berechtigung fehlt
            content = None
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
            except (PermissionError, IOError):
                # Versuche mit sudo
                try:
                    if sudo_password:
                        # Mit Passwort via stdin
                        process = subprocess.Popen(
                            ["sudo", "-S", "cat", str(config_file)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        stdout, stderr = process.communicate(input=sudo_password + '\n', timeout=5)
                        if process.returncode == 0:
                            content = stdout
                        else:
                            return {
                                "status": "error",
                                "message": f"Konnte config.txt nicht lesen (sudo): {stderr[:200] if stderr else 'Unbekannter Fehler'}",
                                "config": {},
                                "requires_sudo_password": True
                            }
                    else:
                        # Ohne Passwort (funktioniert nur wenn sudo ohne Passwort konfiguriert ist)
                        result = subprocess.run(
                            ["sudo", "cat", str(config_file)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            content = result.stdout
                        else:
                            return {
                                "status": "error",
                                "message": f"Konnte config.txt nicht lesen (sudo ohne Passwort fehlgeschlagen): {result.stderr[:200] if result.stderr else 'Unbekannter Fehler'}",
                                "config": {},
                                "requires_sudo_password": True
                            }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Fehler beim Lesen der config.txt: {str(e)}",
                        "config": {},
                        "requires_sudo_password": not sudo_password
                    }
            
            if content is None:
                return {
                    "status": "error",
                    "message": "Konnte config.txt nicht lesen (keine Berechtigung)",
                    "config": {},
                    "requires_sudo_password": True
                }
            
            # Parse Inhalt
            for line in content.splitlines():
                line = line.strip()
                # Kommentare und leere Zeilen überspringen
                if not line or line.startswith('#'):
                    continue
                
                # Parse Zeile: key=value oder key=value # comment
                if '=' in line:
                    parts = line.split('#', 1)[0].strip()  # Kommentar entfernen
                    key, value = parts.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Bool-Werte konvertieren
                    if value.lower() in ('on', '1', 'true', 'yes'):
                        value = True
                    elif value.lower() in ('off', '0', 'false', 'no'):
                        value = False
                    
                    config[key] = value
            
            return {
                "status": "success",
                "config": config,
                "file": str(config_file)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler beim Lesen der Konfiguration: {str(e)}",
                "config": {}
            }
    
    def write_config(self, config: Dict[str, Any], sudo_password: str = "") -> Dict[str, Any]:
        """Schreibt die Konfiguration"""
        config_file = self.get_config_file()
        def _stdin() -> Optional[bytes]:
            return (sudo_password + "\n").encode("utf-8") if sudo_password else None
        use_sudo_s = bool(sudo_password)
        _cmd = ["sudo", "-S", "cp"] if use_sudo_s else ["sudo", "cp"]
        _cmd_mv = ["sudo", "-S", "mv"] if use_sudo_s else ["sudo", "mv"]
        
        try:
            # Backup erstellen
            backup_file = config_file.with_suffix('.txt.backup')
            if config_file.exists():
                subprocess.run(
                    _cmd + [str(config_file), str(backup_file)],
                    check=True,
                    input=_stdin(),
                    capture_output=True,
                    timeout=10,
                )
            
            # Neue Konfiguration schreiben
            lines = []
            lines.append("# Raspberry Pi Konfiguration - Generiert von PI-Installer\n")
            lines.append("# Änderungen an dieser Datei erfordern einen Neustart\n\n")
            
            for key, value in sorted(config.items()):
                if value is True:
                    lines.append(f"{key}=on\n")
                elif value is False:
                    lines.append(f"{key}=off\n")
                elif value is None or value == "":
                    continue  # Überspringe leere Werte
                else:
                    lines.append(f"{key}={value}\n")
            
            # Temporäre Datei schreiben
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
                tmp.writelines(lines)
                tmp_path = tmp.name
            
            # Mit sudo verschieben
            subprocess.run(
                _cmd_mv + [tmp_path, str(config_file)],
                check=True,
                input=_stdin(),
                capture_output=True,
                timeout=10,
            )
            
            return {
                "status": "success",
                "message": "Konfiguration gespeichert",
                "file": str(config_file),
                "backup": str(backup_file)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler beim Schreiben der Konfiguration: {str(e)}"
            }
    
    def get_config_option_info(self, key: str) -> Dict[str, Any]:
        """Gibt Informationen zu einer Konfigurationsoption zurück"""
        if key in self.config_options:
            return {
                "status": "success",
                "option": self.config_options[key]
            }
        else:
            return {
                "status": "error",
                "message": f"Unbekannte Option: {key}"
            }
    
    def _detect_pi_model(self) -> Dict[str, Any]:
        """Erkennt das Raspberry Pi Modell und RAM-Größe"""
        model_str = ""
        ram_mb = 0
        
        # Modell aus /proc/device-tree/model lesen
        for p in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
            try:
                b = Path(p).read_bytes()
                if b:
                    model_str = b.decode("utf-8", errors="ignore").strip("\x00").strip()
                    break
            except Exception:
                continue
        
        # RAM-Größe ermitteln
        try:
            memory = psutil.virtual_memory()
            ram_mb = memory.total // (1024 * 1024)  # Bytes zu MB
        except Exception:
            pass
        
        # Modell-Parsing
        pi_model = "unknown"
        pi_generation = 0
        
        if "Raspberry Pi" in model_str:
            model_lower = model_str.lower()
            if "pi 5" in model_lower or "pi5" in model_lower:
                pi_model = "pi5"
                pi_generation = 5
            elif "pi 4" in model_lower or "pi4" in model_lower:
                pi_model = "pi4"
                pi_generation = 4
            elif "pi 3" in model_lower or "pi3" in model_lower:
                pi_model = "pi3"
                pi_generation = 3
            elif "pi 2" in model_lower or "pi2" in model_lower:
                pi_model = "pi2"
                pi_generation = 2
            elif "pi 1" in model_lower or "pi 1" in model_lower or "pi zero" in model_lower:
                pi_model = "pi1"
                pi_generation = 1
        
        return {
            "model_string": model_str,
            "model": pi_model,
            "generation": pi_generation,
            "ram_mb": ram_mb,
            "ram_gb": round(ram_mb / 1024, 2) if ram_mb > 0 else 0
        }
    
    def _is_option_compatible(self, option_key: str, option_data: Dict[str, Any], pi_info: Dict[str, Any]) -> bool:
        """Prüft ob eine Option mit dem aktuellen Pi kompatibel ist"""
        # Optionen für 256MB Pi ausschließen (veraltet)
        if "256" in option_key.lower() or "_256" in option_key:
            return False
        
        # Optionen für 512MB Pi ausschließen (veraltet)
        if "512" in option_key.lower() and "gpu_mem_512" in option_key:
            return False
        
        # Pi3-spezifische Optionen nur für Pi3 anzeigen
        if "pi3" in option_key.lower() and pi_info["generation"] != 3:
            return False
        
        # Pi-spezifische Overlays nur für passende Generation
        if "dtoverlay=pi3-" in option_key and pi_info["generation"] != 3:
            return False
        
        # GPU-Memory-Optionen: gpu_mem_256 und gpu_mem_512 ausschließen
        if option_key in ("gpu_mem_256", "gpu_mem_512"):
            return False
        
        # Raspberry Pi Control Center Optionen ausschließen (nicht relevant)
        if "control" in option_key.lower() or "center" in option_key.lower():
            return False
        
        return True
    
    def _group_options_by_category(self, options: Dict[str, Dict[str, Any]]) -> Dict[str, List[tuple]]:
        """Gruppiert Optionen nach Kategorien"""
        categories = {
            "gpu": [],
            "overclocking": [],
            "hdmi": [],
            "display": [],
            "gpio": [],
            "camera": [],
            "wireless": [],
            "other": []
        }
        
        category_names = {
            "gpu": "GPU & Video",
            "overclocking": "Overclocking & Performance",
            "hdmi": "HDMI",
            "display": "Display & Framebuffer",
            "gpio": "GPIO & Schnittstellen",
            "camera": "Kamera",
            "wireless": "WiFi & Bluetooth",
            "other": "Sonstiges"
        }
        
        # Reihenfolge der Kategorien für die Anzeige
        category_order = ["gpu", "overclocking", "hdmi", "display", "gpio", "camera", "wireless", "other"]
        
        for key, option in options.items():
            category = option.get("category", "other")
            if category not in categories:
                category = "other"
            categories[category].append((key, option))
        
        # Entferne leere Kategorien und sortiere nach vordefinierter Reihenfolge
        result = {}
        for cat in category_order:
            if cat in categories and categories[cat]:
                result[cat] = {
                    "name": category_names.get(cat, cat),
                    "options": categories[cat]
                }
        
        return result
    
    def get_all_config_options(self, filter_by_model: bool = True) -> Dict[str, Any]:
        """Gibt alle verfügbaren Konfigurationsoptionen zurück, gefiltert nach Pi-Modell und gruppiert nach Kategorien"""
        if not filter_by_model:
            return {
                "status": "success",
                "options": self.config_options,
                "categories": self._group_options_by_category(self.config_options)
            }
        
        pi_info = self._detect_pi_model()
        filtered_options = {}
        
        for key, option in self.config_options.items():
            if self._is_option_compatible(key, option, pi_info):
                filtered_options[key] = option
        
        return {
            "status": "success",
            "options": filtered_options,
            "categories": self._group_options_by_category(filtered_options),
            "pi_info": pi_info
        }
    
    def validate_config_value(self, key: str, value: Any) -> Dict[str, Any]:
        """Validiert einen Konfigurationswert"""
        if key not in self.config_options:
            return {
                "status": "error",
                "message": f"Unbekannte Option: {key}"
            }
        
        option = self.config_options[key]
        option_type = option.get("type", "str")
        
        if option_type == "bool":
            if isinstance(value, bool):
                return {"status": "success"}
            elif isinstance(value, str):
                if value.lower() in ('on', 'off', '1', '0', 'true', 'false', 'yes', 'no'):
                    return {"status": "success"}
            return {"status": "error", "message": f"Ungültiger Bool-Wert: {value}"}
        
        elif option_type == "int":
            try:
                int_val = int(value)
                if "range" in option:
                    min_val, max_val = option["range"]
                    if min_val <= int_val <= max_val:
                        return {"status": "success"}
                    else:
                        return {
                            "status": "error",
                            "message": f"Wert muss zwischen {min_val} und {max_val} liegen"
                        }
                return {"status": "success"}
            except (ValueError, TypeError):
                return {"status": "error", "message": f"Ungültiger Integer-Wert: {value}"}
        
        elif option_type == "str":
            if "options" in option:
                if value in option["options"]:
                    return {"status": "success"}
                else:
                    return {
                        "status": "error",
                        "message": f"Wert muss einer von {option['options']} sein"
                    }
            return {"status": "success"}
        
        return {"status": "success"}
