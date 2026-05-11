#!/usr/bin/env python3
"""
PI-Installer DSI Radio – Standalone PyQt6-App für Freenove 4,3" DSI.
Version 2.0: GStreamer-Wiedergabe (statt VLC/mpv). 20 Favoriten, Radio-Browser-API, Klavierlack-Design.
Wayfire: Fenstertitel „Sabrina Tuner“ → start_on_output DSI-1 (TFT).
"""

# Radio-App-Version (2.1 = NDR-Stream-Preferenz, Ausgabe nur auf Freenove erzwungen)
RADIO_APP_VERSION = "2.1.0"

import os
import sys
import json
import random
import subprocess
import threading
import urllib.request
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QSizePolicy,
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QMessageBox,
    QGridLayout,
    QSlider,
    QSizeGrip,
)
from PyQt6.QtCore import Qt, QTimer, QByteArray, QRectF, QBuffer, QIODevice, QMimeData, QMetaObject, Q_ARG, QThread, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush, QColor, QImage, QShortcut, QKeySequence, QIcon
from math import pi, cos, sin, log, exp

try:
    import numpy as np
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

# GStreamer-Player (Version 2.0)
try:
    from . import gst_player
except ImportError:
    import gst_player

BACKEND_BASE = os.environ.get("PI_INSTALLER_BACKEND", "http://127.0.0.1:8000")
METADATA_INTERVAL_MS = 15000  # 15 Sekunden (reduziert Last auf Backend)
CLOCK_INTERVAL_MS = 1000
WINDOW_TITLE = "Sabrina Tuner"
# Konfigurationsverzeichnis: absolut, damit es immer korrekt ist
_CONFIG_BASE = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_DIR = os.path.join(_CONFIG_BASE, "pi-installer-dsi-radio")
# Projektroot (Linux): für Anzeige von Installationspfaden in Fehlermeldungen
_DSI_RADIO_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_DSI_RADIO_DIR, "..", ".."))
_INSTALL_SCRIPT = os.path.join(_REPO_ROOT, "scripts", "install-dsi-radio-setup.sh")
# Stelle sicher, dass Verzeichnis existiert
os.makedirs(CONFIG_DIR, exist_ok=True)
FAVORITES_FILE = os.path.join(CONFIG_DIR, "favorites.json")
LAST_STATION_FILE = os.path.join(CONFIG_DIR, "last_station.json")
THEME_FILE = os.path.join(CONFIG_DIR, "theme.txt")
DISPLAY_CONFIG_FILE = os.path.join(CONFIG_DIR, "display.json")
ICONS_CONFIG_FILE = os.path.join(CONFIG_DIR, "icons.json")
RADIO_STATIONS_CACHE_FILE = os.path.join(CONFIG_DIR, "radio_stations_cache.json")
# Sender-Buttons fließen in den freien Raum (Spalten aus Breite), max 16 pro Seite
FAVORITES_PER_PAGE = 16
FAVORITES_PER_PAGE_DESKTOP = 16
FAVORITES_MAX = 64
# Button 80px + Abstand 6px für Berechnung der Spalten
STATION_BTN_WIDTH, STATION_BTN_SPACING = 80, 6

try:
    from stations import RADIO_STATIONS, STATION_LOGO_FALLBACKS
    # Zusatz-Fallbacks für Namen aus API/Favoriten (DLF, DFL, BR24)
    _dlf_url = next((s.get("logo_url", "") for s in RADIO_STATIONS if (s.get("name") or "").strip() == "Deutschlandfunk"), "")
    if _dlf_url:
        STATION_LOGO_FALLBACKS["DLF"] = _dlf_url
        STATION_LOGO_FALLBACKS["DFL"] = _dlf_url
    # BR24 eigenständiger Sender (Nachrichten), nicht BR-Klassik
    _br24_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Bayern_2_Logo.svg/512px-Bayern_2_Logo.svg.png"
    STATION_LOGO_FALLBACKS["BR24"] = _br24_url
    _hr1_url = next((s.get("logo_url", "") for s in RADIO_STATIONS if (s.get("name") or "").strip() == "HR1"), "")
    if _hr1_url:
        STATION_LOGO_FALLBACKS["HR 1"] = _hr1_url
    _rbb_url = next((s.get("logo_url", "") for s in RADIO_STATIONS if (s.get("name") or "").strip() == "rbb 88.8"), "")
    if _rbb_url:
        STATION_LOGO_FALLBACKS["rbb 88,8"] = _rbb_url
    _mdr_url = next((s.get("logo_url", "") for s in RADIO_STATIONS if (s.get("name") or "").strip() == "MDR Aktuell"), "")
    if _mdr_url:
        STATION_LOGO_FALLBACKS["MDR Aktuell"] = _mdr_url
    # API-/Favoriten-Varianten (Komma, Langname)
    for s in RADIO_STATIONS:
        logo_url = (s.get("logo_url") or "").strip()
        if not logo_url:
            continue
        name = (s.get("name") or "").strip()
        if name == "104.6 RTL":
            STATION_LOGO_FALLBACKS["104,6 RTL"] = logo_url
        if name == "DLF Kultur":
            STATION_LOGO_FALLBACKS["Deutschlandfunk Kultur"] = logo_url
        if name == "R.SA":
            STATION_LOGO_FALLBACKS["R.SA"] = logo_url
        if name == "Radio Bob":
            STATION_LOGO_FALLBACKS["Radio Bob"] = logo_url
except ImportError:
    RADIO_STATIONS = [
        {"id": "einslive", "name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "wdr2", "name": "WDR 2", "stream_url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "dlf", "name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "logo_url": "", "region": "Bundesweit", "genre": "Info"},
        {"id": "rsa", "name": "R.SA", "stream_url": "http://streams.rsa-sachsen.de/rsa-live/mp3-192/rsamediaplayer", "logo_url": "", "region": "Sachsen", "genre": "Pop"},
        {"id": "radiosaw", "name": "Radio SAW", "stream_url": "https://stream.radiosaw.de/saw/mp3-192/radio-browser/", "logo_url": "", "region": "Sachsen-Anhalt", "genre": "Pop"},
    ]
    STATION_LOGO_FALLBACKS = {}


def _find_player() -> Optional[str]:
    for cmd in ("cvlc", "mpv", "mpg123"):
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
            return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _player_cmd_prefix() -> List[str]:
    """Wenn die App als root läuft (z. B. sudo): Prefix um den Player als normalen Benutzer zu starten.
    VLC weigert sich, als root zu laufen ('VLC is not supposed to be run as root')."""
    try:
        if os.geteuid() != 0:
            return []
        sudo_user = os.environ.get("SUDO_USER")
        if not sudo_user:
            return []
        home = os.path.expanduser(f"~{sudo_user}") if sudo_user else f"/home/{sudo_user}"
        try:
            import pwd
            uid = pwd.getpwnam(sudo_user).pw_uid
            xdg = f"/run/user/{uid}"
        except Exception:
            xdg = os.environ.get("XDG_RUNTIME_DIR", "")
        env_parts = [
            f"DISPLAY={os.environ.get('DISPLAY', ':0')}",
            f"XDG_RUNTIME_DIR={xdg}",
            f"HOME={home}",
            f"PULSE_RUNTIME_PATH={xdg}" if xdg else "",
        ]
        env_parts = [e for e in env_parts if e and "=" in e and not e.endswith("=")]
        return ["sudo", "-n", "-u", sudo_user, "env"] + env_parts
    except Exception:
        return []


def _pactl_env():
    """Umgebung für pactl: PATH mit /usr/bin, damit Desktop-Start pactl findet."""
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin:" + env.get("PATH", "")
    return env


def _pactl_path() -> Optional[str]:
    """Pactl-Befehl (PulseAudio/PipeWire). Zuerst which, sonst /usr/bin/pactl."""
    env = _pactl_env()
    for candidate in ("pactl", "/usr/bin/pactl"):
        try:
            if candidate == "pactl":
                r = subprocess.run(["which", "pactl"], capture_output=True, timeout=1, env=env)
                if r.returncode != 0:
                    continue
                return "pactl"
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        except Exception:
            continue
    return None


def _get_system_stream_metadata() -> dict:
    """Liest Titel/Interpret aus dem Lautstärkeregler-System (PulseAudio/PipeWire).
    pactl list sink-inputs liefert media.title, media.artist für unseren Prozess –
    dieselbe Quelle wie der System-OSD. Gibt dict mit title, artist, show zurück (leer wenn nichts)."""
    out: dict = {}
    pactl = _pactl_path()
    if not pactl:
        return out
    pid_str = str(os.getpid())
    try:
        result = subprocess.run(
            [pactl, "list", "sink-inputs"],
            capture_output=True,
            text=True,
            timeout=3,
            env=_pactl_env(),
        )
        if result.returncode != 0 or not result.stdout:
            return out
        # Blöcke nach "Sink Input #N" trennen; in jedem Block nach application.process.id = "PID" suchen
        blocks = result.stdout.split("Sink Input #")
        for block in blocks:
            if not block.strip():
                continue
            # Nur unseren Prozess (application.process.id = "12345")
            if f'application.process.id = "{pid_str}"' not in block and f"application.process.id = {pid_str}" not in block:
                continue
            # In diesem Block Properties parsen: media.title = "..." oder media.artist = "..."
            in_props = False
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("Properties:"):
                    in_props = True
                    continue
                if in_props and "=" in line:
                    # Nächster Abschnitt (z. B. "Format:") beendet Properties
                    if line.startswith(("Format", "Cork", "Mute", "Volume", "Buffer", "Latency", "State")):
                        break
                    key, _, rest = line.partition("=")
                    key = key.strip().rstrip(":")
                    val = rest.strip().strip('"').strip()
                    if key == "media.title" and val:
                        out["title"] = val
                    elif key == "media.artist" and val:
                        out["artist"] = val
                    elif key == "media.name" and val and "show" not in out:
                        out["show"] = val
            break
    except Exception:
        pass
    return out


def _find_audio_sink() -> Optional[str]:
    """Findet das richtige PulseAudio/PipeWire-Sink.
    Freenove: Gehäuselautsprecher/Media-Board = System-Standard-Sink (Einstellungen → Sound).
    Priorität: 1. Bei 2 Sinks den anderen als Standard (Gehäuse), 2. Standard-Sink, 3. Nicht-HDMI, 4. HDMI-1-2.
    Gibt den Sink-Namen zurück (für PulseAudio/PipeWire)."""
    pactl = _pactl_path()
    if not pactl:
        try:
            debug_file = os.path.join(CONFIG_DIR, "audio_sink_error.log")
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: pactl nicht gefunden (which + /usr/bin/pactl)\n")
        except Exception:
            pass
        return None
    env = _pactl_env()
    try:
        result = subprocess.run(
            [pactl, "list", "short", "sinks"],
            capture_output=True, text=True, timeout=2, env=env
        )
        if result.returncode != 0:
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(os.path.join(CONFIG_DIR, "audio_sink_error.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: pactl list short sinks returncode={result.returncode} stderr={result.stderr[:200] if result.stderr else ''}\n")
            except Exception:
                pass
            return None
        lines = result.stdout.strip().split("\n")
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(os.path.join(CONFIG_DIR, "audio_sink_selected.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: pactl list short sinks: {len(lines)} Zeilen\n")
                for ln in lines[:20]:
                    f.write(f"  {ln}\n")
        except Exception:
            pass
        all_sink_names = []
        sink_index_map = {}  # Name -> Index für VLC
        sink_alsa_card_map = {}  # Name -> ALSA card number
        
        # ALSA card-Nummern für jeden Sink ermitteln
        try:
            result_detailed = subprocess.run(
                [pactl, "list", "sinks"],
                capture_output=True, text=True, timeout=3, env=env
            )
            if result_detailed.returncode == 0:
                current_sink = None
                for line_detail in result_detailed.stdout.split("\n"):
                    line_stripped = line_detail.strip()
                    if line_stripped.startswith("Name:"):
                        current_sink = line_stripped.split(":", 1)[1].strip()
                    elif current_sink and "alsa.card" in line_stripped:
                        try:
                            # Format: "alsa.card = "0"" oder "alsa.card = 0"
                            parts = line_stripped.split("=", 1)
                            if len(parts) == 2:
                                card_str = parts[1].strip().strip('"').strip("'")
                                card_num = int(card_str)
                                sink_alsa_card_map[current_sink] = card_num
                        except (ValueError, IndexError):
                            pass
        except Exception:
            pass
        
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                sink_name = parts[1].strip()
                all_sink_names.append(sink_name)
                if len(parts) >= 1:
                    try:
                        sink_index = int(parts[0].strip())
                        sink_index_map[sink_name] = sink_index
                    except (ValueError, IndexError):
                        pass

        # Default-Sink
        default_sink = ""
        try:
            r = subprocess.run(
                [pactl, "get-default-sink"],
                capture_output=True, text=True, timeout=2, env=env
            )
            if r.returncode == 0 and r.stdout and r.stdout.strip():
                default_sink = r.stdout.strip()
        except Exception:
            pass

        # WICHTIG: Gehäuselautsprecher sind NICHT an HDMI angeschlossen!
        # Suche nach Non-HDMI-Ausgängen: analog, headphone, speaker, 3.5mm, etc.
        non_hdmi_sinks = []
        analog_sinks = []
        headphone_sinks = []
        speaker_sinks = []
        hdmi_sinks = []
        all_sinks = []
        
        # Detaillierte Sink-Informationen für bessere Erkennung
        sink_descriptions = {}
        try:
            result_detailed = subprocess.run(
                [pactl, "list", "sinks"],
                capture_output=True, text=True, timeout=3, env=env
            )
            if result_detailed.returncode == 0:
                current_sink = None
                for line_detail in result_detailed.stdout.split("\n"):
                    line_stripped = line_detail.strip()
                    if line_stripped.startswith("Name:"):
                        current_sink = line_stripped.split(":", 1)[1].strip()
                    elif current_sink and line_stripped.startswith("Description:"):
                        desc = line_stripped.split(":", 1)[1].strip()
                        sink_descriptions[current_sink] = desc
        except Exception:
            pass

        for line in lines:
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                sink_name = parts[1].strip()
                all_sinks.append(sink_name)
                sink_lower = sink_name.lower()
                desc_lower = sink_descriptions.get(sink_name, "").lower()
                combined = f"{sink_name} {desc_lower}".lower()
                
                # HDMI-Ausgänge identifizieren und AUSSCHLIESSEN
                is_hdmi = (
                    "hdmi" in sink_lower or
                    "107c701400" in sink_name or
                    "107c706400" in sink_name or
                    "vc4hdmi" in sink_lower or
                    "digital stereo (hdmi)" in desc_lower
                )
                
                if is_hdmi:
                    hdmi_sinks.append(sink_name)
                else:
                    # Non-HDMI-Ausgänge kategorisieren
                    non_hdmi_sinks.append(sink_name)
                    
                    # Spezifische Kategorien für Gehäuselautsprecher
                    if ("analog" in combined or "3.5" in combined or "jack" in combined or
                        "headphone" in combined or "headphones" in combined):
                        headphone_sinks.append(sink_name)
                    if ("speaker" in combined or "lautsprecher" in combined or 
                        "gehäuse" in combined or "case" in combined):
                        speaker_sinks.append(sink_name)
                    if ("analog" in combined and "output" in combined):
                        analog_sinks.append(sink_name)

        # PRIORITÄT 1: Speaker/Gehäuselautsprecher (explizit)
        if speaker_sinks:
            selected_sink = speaker_sinks[0]
            try:
                df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                with open(df, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: PRIORITÄT 1 - Speaker/Gehäuselautsprecher: {selected_sink}\n")
                    f.write(f"  Gefundene Speaker-Sinks: {speaker_sinks}\n")
                    f.write(f"  Gefundene Headphone-Sinks: {headphone_sinks}\n")
                    f.write(f"  Gefundene Analog-Sinks: {analog_sinks}\n")
                    f.write(f"  Gefundene Non-HDMI-Sinks: {non_hdmi_sinks}\n")
                    f.write(f"  HDMI-Sinks (ausgeschlossen): {hdmi_sinks}\n")
            except Exception:
                pass
            return selected_sink

        # PRIORITÄT 2: Headphone/3.5mm Ausgänge
        if headphone_sinks:
            selected_sink = headphone_sinks[0]
            try:
                df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                with open(df, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: PRIORITÄT 2 - Headphone/3.5mm: {selected_sink}\n")
            except Exception:
                pass
            return selected_sink

        # PRIORITÄT 3: Analog-Ausgänge
        if analog_sinks:
            selected_sink = analog_sinks[0]
            try:
                df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                with open(df, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: PRIORITÄT 3 - Analog: {selected_sink}\n")
            except Exception:
                pass
            return selected_sink

        # PRIORITÄT 4: Alle Non-HDMI-Ausgänge
        if non_hdmi_sinks:
            selected_sink = non_hdmi_sinks[0]
            try:
                df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                with open(df, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: PRIORITÄT 4 - Non-HDMI: {selected_sink}\n")
                    f.write(f"  WARNUNG: Kein expliziter Speaker/Headphone/Analog-Ausgang gefunden!\n")
                    f.write(f"  Verfügbare Non-HDMI-Sinks: {non_hdmi_sinks}\n")
                    f.write(f"  HDMI-Sinks (ausgeschlossen): {hdmi_sinks}\n")
            except Exception:
                pass
            return selected_sink

        # FREENOVE: Bei Freenove Computer Case extrahiert das Mediaboard Audio aus HDMI
        # WICHTIG: Das Mediaboard muss über den richtigen HDMI-Port angesprochen werden,
        # damit das Audio an die Gehäuselautsprecher weitergeleitet wird (nicht an HDMI-Monitor)
        # In Version 1.2.x.x wurde der Standard-Sink verwendet, der automatisch richtig geroutet wurde
        if hdmi_sinks:
            # Prüfe ob Freenove-Gehäuse erkannt wird (I2C Expansion-Board)
            is_freenove = False
            try:
                for bus in (1, 0, 6, 7):
                    result_i2c = subprocess.run(
                        ["i2cget", "-y", str(bus), "0x21", "0xfd"],
                        capture_output=True,
                        timeout=1
                    )
                    if result_i2c.returncode == 0:
                        is_freenove = True
                        break
            except Exception:
                pass
            
            if is_freenove:
                # Bei Freenove: Verwende den Standard-Sink (wie in Version 1.2.x.x)
                # Das Mediaboard routet automatisch an die Gehäuselautsprecher
                if default_sink and default_sink in hdmi_sinks:
                    selected_sink = default_sink
                    try:
                        df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                        with open(df, "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now().isoformat()}: FREENOVE - Standard-Sink verwendet (wie Version 1.2.x.x)\n")
                            f.write(f"  Standard-Sink: {selected_sink}\n")
                            f.write(f"  Verfügbare HDMI-Sinks: {hdmi_sinks}\n")
                            f.write(f"  Hinweis: Mediaboard extrahiert Audio aus HDMI und routet an Gehäuselautsprecher.\n")
                    except Exception:
                        pass
                    return selected_sink
                
                # Fallback: HDMI0 (107c701400) - primärer HDMI-Port
                selected_sink = None
                for sink in hdmi_sinks:
                    if "107c701400" in sink:
                        selected_sink = sink
                        break
                # Fallback: Erster HDMI-Sink
                if not selected_sink:
                    selected_sink = hdmi_sinks[0]
                
                try:
                    df = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                    with open(df, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()}: FREENOVE - HDMI-Ausgang verwendet (Fallback)\n")
                        f.write(f"  Ausgewählter HDMI-Sink: {selected_sink}\n")
                        f.write(f"  Verfügbare HDMI-Sinks: {hdmi_sinks}\n")
                        f.write(f"  Standard-Sink war: {default_sink}\n")
                except Exception:
                    pass
                
                return selected_sink
            else:
                # Kein Freenove-Gehäuse: Priorität HDMI0 (107c701400)
                selected_sink = None
                for sink in hdmi_sinks:
                    if "107c701400" in sink:
                        selected_sink = sink
                        break
                if not selected_sink:
                    selected_sink = hdmi_sinks[0]
                return selected_sink
        
        # FEHLER: Keine Audio-Ausgänge gefunden
        try:
            df = os.path.join(CONFIG_DIR, "audio_sink_error.log")
            with open(df, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: FEHLER - Keine Audio-Ausgänge gefunden!\n")
                f.write(f"  Verfügbare Sinks: {all_sinks}\n")
                f.write(f"  Bitte prüfen Sie die Audio-Konfiguration.\n")
        except Exception:
            pass
        
        return None  # Kein passender Ausgang gefunden
    except Exception as e:
        # Debug: Fehler in Datei schreiben
        try:
            debug_file = os.path.join(CONFIG_DIR, "audio_sink_error.log")
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: Audio-Sink-Fehler: {type(e).__name__}: {str(e)}\n")
        except Exception:
            pass
    return None


def _normalize_favorite_url(url: str) -> str:
    """URL für Favoriten-Vergleich normalisieren (trailing slash, Leerzeichen)."""
    u = (url or "").strip().rstrip("/")
    return u


def _deduplicate_favorites_by_url(stations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Entfernt doppelte Sender (gleiche stream_url), z. B. NDR 1 unter verschiedenen Namen."""
    seen_urls = set()
    out = []
    for s in stations:
        url = (s.get("stream_url") or s.get("url") or "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            out.append(s)
    return out


def _deduplicate_favorites_ndr(stations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Behält pro NDR 1 bzw. NDR 2 nur einen Eintrag (ersten), Doppelte wie „NDR 1 Niedersachsen“ und „NDR 1 Welle Nord“ entfernt."""
    out = []
    seen_ndr1 = False
    seen_ndr2 = False
    for s in stations:
        name = (s.get("name") or "").strip()
        if "NDR 1" in name:
            if seen_ndr1:
                continue
            seen_ndr1 = True
        elif "NDR 2" in name:
            if seen_ndr2:
                continue
            seen_ndr2 = True
        out.append(s)
    return out


def load_favorites() -> List[Dict[str, Any]]:
    try:
        if os.path.isfile(FAVORITES_FILE):
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    dedup = _deduplicate_favorites_by_url(data[:FAVORITES_MAX])
                    dedup = _deduplicate_favorites_ndr(dedup)
                    return dedup
    except Exception:
        pass
    default = [{"id": s["id"], "name": s["name"], "stream_url": s["stream_url"], "logo_url": s.get("logo_url", ""), "region": s.get("region", ""), "genre": s.get("genre", "")} for s in RADIO_STATIONS[:FAVORITES_MAX]]
    return _deduplicate_favorites_ndr(_deduplicate_favorites_by_url(default))


def save_favorites(stations: List[Dict[str, Any]]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump(stations[:FAVORITES_MAX], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_last_station() -> Optional[Dict[str, Any]]:
    """Letzten gespielten Sender laden (für Start mit letztem Sender)."""
    try:
        if os.path.isfile(LAST_STATION_FILE):
            with open(LAST_STATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and (data.get("stream_url") or data.get("url")):
                    if not data.get("stream_url") and data.get("url"):
                        data["stream_url"] = data["url"]
                    return data
    except Exception:
        pass
    return None


def save_last_station(station: Dict[str, Any]) -> None:
    """Letzten gespielten Sender speichern."""
    if not station or not (station.get("stream_url") or station.get("url")):
        return
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        out = {k: v for k in ("id", "name", "stream_url", "url", "logo_url", "region", "genre") for v in (station.get(k),) if v is not None}
        if not (out.get("stream_url") or out.get("url")):
            return
        with open(LAST_STATION_FILE, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_theme() -> str:
    """Design aus PI-Installer-Konfiguration (theme.txt)."""
    try:
        if os.path.isfile(THEME_FILE):
            with open(THEME_FILE, "r", encoding="utf-8") as f:
                name = (f.read() or "").strip()
                if name in ("Klavierlack", "Classic", "Hell"):
                    return name
    except Exception:
        pass
    return "Klavierlack"


def save_theme(name: str) -> None:
    """Design speichern (wird vom PI-Installer aufgerufen)."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(THEME_FILE, "w", encoding="utf-8") as f:
            f.write(name if name in ("Klavierlack", "Classic", "Hell") else "Klavierlack")
    except Exception:
        pass


def load_display_config() -> dict:
    """Anzeige-Optionen aus display.json (PI-Installer Einstellungen)."""
    out = {"show_clock": True, "vu_mode": "led", "display_max_width": 600, "display_font_scale": 0.85}
    try:
        if os.path.isfile(DISPLAY_CONFIG_FILE):
            with open(DISPLAY_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    out["show_clock"] = data.get("show_clock", True)
                    out["vu_mode"] = data.get("vu_mode", "led") if data.get("vu_mode") in ("led", "analog") else "led"
                    if "display_max_width" in data and isinstance(data["display_max_width"], (int, float)):
                        out["display_max_width"] = max(320, min(1200, int(data["display_max_width"])))
                    if "display_font_scale" in data and isinstance(data["display_font_scale"], (int, float)):
                        s = float(data["display_font_scale"])
                        out["display_font_scale"] = max(0.5, min(1.5, s))
    except Exception:
        pass
    return out


def load_icons_config() -> dict:
    """Icon-Optionen aus icons.json (PI-Installer Einstellungen)."""
    out = {"logo_source": "url", "logo_size": "medium"}
    try:
        if os.path.isfile(ICONS_CONFIG_FILE):
            with open(ICONS_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    out["logo_source"] = data.get("logo_source", "url") if data.get("logo_source") in ("url", "local") else "url"
                    out["logo_size"] = data.get("logo_size", "medium") if data.get("logo_size") in ("small", "medium", "large") else "medium"
    except Exception:
        pass
    return out


def _prefer_stations_py_stream_url(current_station: dict, url: str) -> str:
    """Bevorzugt getestete Stream-URLs aus stations.py (z. B. NDR über icecast.ndr.de statt addradio.de)."""
    if not url or not current_station:
        return url
    cur_name = (current_station.get("name") or "").strip()
    cur_id = (current_station.get("id") or "").strip()
    try:
        for s in RADIO_STATIONS:
            alt = (s.get("stream_url") or s.get("url") or "").strip()
            if not alt:
                continue
            sid = (s.get("id") or "").strip()
            sname = (s.get("name") or "").strip()
            if cur_id and sid and cur_id == sid:
                return alt
            if cur_name == sname:
                return alt
            # NDR 1 / NDR 2: API liefert oft andere Namen („NDR 1 Niedersachsen“) oder addradio-URLs
            if cur_name and sname and "NDR 1" in cur_name and "NDR 1" in sname:
                return alt
            if cur_name and sname and "NDR 2" in cur_name and "NDR 2" in sname:
                return alt
            # HR1 / HR 1 (API-Schreibweise)
            if sname == "HR1" and ("HR1" in cur_name or "HR 1" in cur_name.replace(" ", "").upper() or cur_name.strip().upper() == "HR 1"):
                return alt
            # rbb 88.8 / 88,8
            if sname == "rbb 88.8" and ("88.8" in cur_name or "88,8" in cur_name or "rbb" in cur_name.lower()):
                return alt
            # Energy
            if sname == "Energy" and cur_name.strip().lower() == "energy":
                return alt
    except Exception:
        pass
    return url


def _button_label(name: str, max_chars: int = 12) -> str:
    """Kurzer Button-Text: umbrechen oder Kürzel (touch-tauglich)."""
    if not name:
        return "?"
    name = name.strip()
    if len(name) <= max_chars:
        return name
    # Bekannte Kürzel
    short = {
        "NDR 1 Niedersachsen": "NDR1 NS",
        "NDR 1 Welle Nord": "NDR1 WN",
        "Antenne Bayern": "Ant. Bay.",
        "Deutschlandfunk Kultur": "DLF Kultur",
        "Deutschlandfunk": "DLF",
        "Bremen Zwei": "Bremen 2",
        "104.6 RTL": "104.6 RTL",
        "Rock Antenne": "Rock Ant.",
        "radioeins": "radioeins",
    }
    if name in short:
        return short[name]
    # Erste zwei Wörter oder Kürzel aus Anfangsbuchstaben
    parts = name.split()
    if len(parts) >= 2 and len(parts[0]) + 1 + len(parts[1]) <= max_chars:
        return parts[0] + " " + parts[1]
    if len(parts) >= 2:
        return (parts[0][:2] + parts[1][:2]).upper() if len(parts[0]) >= 2 else name[:max_chars]
    return name[:max_chars]


def _fetch_metadata(url: str) -> dict:
    """Holt Metadaten vom Backend. Pfad für Logs: CONFIG_DIR (~/.config/pi-installer-dsi-radio)."""
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/radio/stream-metadata?url={urllib.request.quote(url, safe='')}",
            headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.load(resp)
            if isinstance(data, dict):
                if "status" in data:
                    del data["status"]
                if os.environ.get("PI_INSTALLER_DSI_DEBUG"):
                    try:
                        os.makedirs(CONFIG_DIR, exist_ok=True)
                        p = os.path.join(CONFIG_DIR, "metadata_debug.json")
                        with open(p, "w", encoding="utf-8") as f:
                            json.dump({"url": url, "metadata": data, "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
                    except Exception:
                        pass
                return data
    except Exception as e:
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            p = os.path.join(CONFIG_DIR, "metadata_error.log")
            with open(p, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: {type(e).__name__}: {str(e)}\n")
        except Exception:
            pass
    return {}


def _fetch_icy_metadata_direct(url: str) -> dict:
    """Liest ICY-Metadaten direkt aus dem Stream (ohne Backend). Fallback wenn Backend leer liefert."""
    def strip_icy(s: str) -> str:
        for q in ("'", '"', "\u2018", "\u2019"):
            if s.startswith(q) and s.endswith(q):
                s = s[1:-1].strip()
                break
        return s.replace("\x00", "").strip()

    def parse_stream_title(raw: str) -> dict | None:
        out = {}
        for part in raw.split(";"):
            part = part.strip()
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            key = key.strip().lower()
            val = strip_icy(val.strip())
            if key and val:
                out[key] = val
        val = out.get("streamtitle", "").strip()
        if not val or len(val) < 3:
            return None
        artist, song = "", val
        for sep in (" - ", " – ", " \u2013 "):
            if sep in val:
                parts = val.split(sep, 1)
                artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                song = (parts[1].strip() or val) if len(parts) > 1 else val
                break
        return {"title": val, "artist": artist, "song": song}

    try:
        timeout = 10 if ("ndr" in url.lower() or "rsa-sachsen" in url.lower() or "radiosaw" in url.lower()) else 5
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0", "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            meta_int = resp.headers.get("icy-metaint")
            if not meta_int:
                return {}
            bitrate = None
            try:
                br = resp.headers.get("icy-br")
                if br:
                    bitrate = int(str(br).strip())
            except (ValueError, TypeError):
                pass
            meta_int = int(meta_int)
            for _ in range(8):
                resp.read(meta_int)
                raw = resp.read(1)
                if not raw:
                    break
                block_len = ord(raw) * 16
                if block_len <= 0:
                    continue
                meta_bytes = resp.read(block_len)
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        text = meta_bytes.decode(enc, errors="strict").strip("\x00").strip()
                    except Exception:
                        continue
                    parsed = parse_stream_title(text)
                    if parsed:
                        if bitrate is not None:
                            parsed["bitrate"] = bitrate
                        return parsed
                text = meta_bytes.decode("utf-8", errors="replace").strip("\x00").strip()
                parsed = parse_stream_title(text)
                if parsed:
                    if bitrate is not None:
                        parsed["bitrate"] = bitrate
                    return parsed
    except Exception:
        pass
    return {}


def _fetch_logo(url: str, name: Optional[str] = None) -> Optional[bytes]:
    """Logo laden: zuerst Backend (DB → extern → Wikipedia), sonst Direktabruf."""
    params: List[str] = []
    if (url or "").strip():
        params.append("url=" + urllib.request.quote(url.strip(), safe=""))
    if (name or "").strip():
        params.append("name=" + urllib.request.quote(name.strip(), safe=""))
    if params:
        try:
            proxy_url = f"{BACKEND_BASE}/api/radio/logo?{'&'.join(params)}"
            req = urllib.request.Request(proxy_url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read()
        except Exception:
            pass
    if not url:
        return None
    try:
        ua = "PI-Installer/1.0 (Radio logo; +https://github.com)" if ("wikipedia.org" in url or "wikimedia.org" in url) else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.read()
    except Exception:
        return None


# Radio-Browser-API direkt (Fallback wenn Backend nicht erreichbar)
RADIO_BROWSER_API_MIRRORS = [
    "https://de1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
]


def _fetch_stations_from_radio_browser_direct(name: str = "", limit: int = 200) -> List[Dict[str, Any]]:
    """Ruft radio-browser.info API direkt auf (ohne Backend). Liefert normierte Senderliste."""
    params = ["country=Germany", "limit=" + str(min(limit, 500))]
    if name.strip():
        params.append("name=" + urllib.request.quote(name.strip()))
    for base in RADIO_BROWSER_API_MIRRORS:
        try:
            url = f"{base}/json/stations/search?{'&'.join(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "DSI-Radio/1.0 (radio-browser.info)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            if not isinstance(data, list):
                continue
            out = []
            for s in data:
                if not isinstance(s, dict):
                    continue
                if s.get("codec") != "MP3" or not s.get("lastcheckok"):
                    continue
                url_resolved = (s.get("url_resolved") or s.get("url") or "").strip()
                if not url_resolved or url_resolved.startswith("m3u"):
                    continue
                out.append({
                    "name": (s.get("name") or "").strip(),
                    "url": url_resolved,
                    "favicon": (s.get("favicon") or "").strip() or None,
                    "state": s.get("state") or "",
                    "tags": s.get("tags") or "",
                })
            return out[:limit]
        except Exception:
            continue
    return []


def _fetch_stations_search(name: str = "") -> List[Dict[str, Any]]:
    """Holt Sender: zuerst Backend (proxy zu radio-browser), bei Fehler direkt radio-browser.info, dann Cache."""
    # 1) Backend (gleicher Parameter wie Backend: country=Germany)
    try:
        url = f"{BACKEND_BASE}/api/radio/stations/search?country=Germany&limit=200"
        if name.strip():
            url += "&name=" + urllib.request.quote(name.strip())
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            stations = []
            if isinstance(data, dict) and "stations" in data:
                stations = data["stations"] if isinstance(data["stations"], list) else []
            elif isinstance(data, list):
                stations = data
            if stations:
                try:
                    with open(RADIO_STATIONS_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump({"stations": stations, "query": name.strip()}, f, ensure_ascii=False)
                except Exception:
                    pass
                return stations
    except Exception:
        pass
    # 2) Direkt radio-browser.info
    direct = _fetch_stations_from_radio_browser_direct(name, 200)
    if direct:
        try:
            with open(RADIO_STATIONS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"stations": direct, "query": name.strip()}, f, ensure_ascii=False)
        except Exception:
            pass
        return direct
    # 3) Gecachte Liste
    try:
        if os.path.isfile(RADIO_STATIONS_CACHE_FILE):
            with open(RADIO_STATIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            stations = cached.get("stations") if isinstance(cached, dict) else []
            if isinstance(stations, list) and stations:
                if name.strip():
                    q = name.strip().lower()
                    stations = [s for s in stations if isinstance(s, dict) and (q in ((s.get("name") or "").lower()))]
                return stations
    except Exception:
        pass
    return []


# --- Designs ---
STYLE_KLAVIERLACK = """
    QMainWindow, QWidget, QDialog { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0c0c0c, stop:1 #1a1a1a); }
    QLabel { color: #e8f4fc; }
    QLineEdit, QListWidget { background: #1e293b; color: #f1f5f9; border: 1px solid #475569; border-radius: 8px; padding: 8px; min-height: 24px; }
    QComboBox { background: #1e293b; color: #f1f5f9; border: 1px solid #475569; border-radius: 8px; padding: 8px; min-height: 24px; }
    QFrame#display { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #14532d, stop:1 #166534);
        border: none; border-radius: 8px;
        padding: 6px; margin: 0; }
    QFrame#display QLabel { color: #0f172a; border: none; }
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2d3748, stop:1 #1a202c);
        color: #f7fafc; border: 2px solid #4a5568;
        border-radius: 12px; padding: 12px 20px; font-size: 14px;
        min-height: 48px;
        border-bottom: 3px solid #2d3748;
    }
    QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3d4a5c, stop:1 #2d3748); border: 2px solid #5a6578; }
    QPushButton:checked { background: #0d9488; color: white; border: 2px solid #0f766e; border-bottom-color: #0f766e; }
    QPushButton#play { min-height: 52px; font-size: 16px; }
"""

STYLE_CLASSIC = """
    QMainWindow, QWidget, QDialog { background-color: #1e293b; }
    QLabel { color: #e2e8f0; }
    QLineEdit, QListWidget, QComboBox { background: #0f172a; color: #e2e8f0; border: 1px solid #475569; border-radius: 8px; padding: 8px; }
    QFrame#display { background-color: #166534; border: none; border-radius: 8px; padding: 6px; margin: 0; }
    QFrame#display QLabel { color: #0f172a; border: none; }
    QPushButton {
        background-color: #334155; color: #f1f5f9; border: 1px solid #475569;
        border-radius: 12px; padding: 12px 20px; font-size: 14px; min-height: 48px;
    }
    QPushButton:hover { background-color: #475569; }
    QPushButton:checked { background-color: #0d9488; color: white; }
    QPushButton#play { min-height: 52px; font-size: 16px; }
"""

STYLE_HELL = """
    QMainWindow, QWidget, QDialog { background-color: #f1f5f9; }
    QLabel { color: #1e293b; }
    QLineEdit, QListWidget, QComboBox { background: #fff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; }
    QFrame#display { background-color: #22c55e; border: none; border-radius: 8px; padding: 6px; margin: 0; }
    QFrame#display QLabel { color: #0f172a; border: none; }
    QPushButton {
        background-color: #cbd5e1; color: #0f172a; border: 1px solid #94a3b8;
        border-radius: 12px; padding: 12px 20px; font-size: 14px; min-height: 48px;
    }
    QPushButton:hover { background-color: #94a3b8; color: white; }
    QPushButton:checked { background-color: #059669; color: white; }
    QPushButton#play { min-height: 52px; font-size: 16px; }
"""

THEMES = {"Klavierlack": STYLE_KLAVIERLACK, "Classic": STYLE_CLASSIC, "Hell": STYLE_HELL}
THEME_NAMES = list(THEMES.keys())


class AnalogGaugeWidget(QWidget):
    """Halbrunde Anzeige L/R: Nullpunkt links (0 %), Skala bis 100 % rechts.
    Rechts roter Hintergrund (Übersteuerung). Zeiger nur 0°–180°. Weisser Hintergrund links."""

    def __init__(self, parent=None, signal_mode: bool = False, size: int = 64):
        super().__init__(parent)
        self._value = 0
        self._signal_mode = signal_mode
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: white; border-radius: 8px;")

    def set_signal_mode(self, on: bool):
        self._signal_mode = on
        self.update()

    def set_value(self, value: int):
        self._value = max(0, min(100, value))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 4
        needle_len = r - 5
        # 0 % = links (180°), 100 % = rechts (0°); Zeiger nur 0°–180°
        def angle_deg(pct):
            return 180 - (pct / 100) * 180

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        painter.fillRect(0, 0, w, h, QColor("white"))
        if self._signal_mode:
            # Signal: rechts (ca. 80–100 %) roter Sektor
            painter.setBrush(QBrush(QColor("#dc2626")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, 108 * 16, -36 * 16)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#64748b"), 1))
            painter.drawArc(rect, 180 * 16, -180 * 16)
        else:
            # VU L/R: rechts (80–100 %) roter Hintergrund
            painter.setBrush(QBrush(QColor("#dc2626")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, 108 * 16, -36 * 16)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#64748b"), 1))
            painter.drawArc(rect, 180 * 16, -180 * 16)
        # Skala: Striche bei 0, 25, 50, 75, 100 %
        painter.setPen(QPen(QColor("#0f172a"), 1))
        for pct in [0, 25, 50, 75, 100]:
            ang_rad = angle_deg(pct) * pi / 180
            x1 = cx + (r - 3) * cos(ang_rad)
            y1 = cy + (r - 3) * sin(ang_rad)
            x2 = cx + r * cos(ang_rad)
            y2 = cy + r * sin(ang_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        # Zeiger: Anzeige begrenzt 0–100 %, Winkel 0°–180°
        display_val = max(0, min(100, self._value))
        ang = angle_deg(display_val) * pi / 180
        x2 = cx + needle_len * cos(ang)
        y2 = cy + needle_len * sin(ang)
        painter.setPen(QPen(QColor("#0f172a"), 2))
        painter.drawLine(int(cx), int(cy), int(x2), int(y2))
        painter.end()


def _fft_to_log_bands(magnitudes: "np.ndarray", num_bands: int) -> List[float]:
    """Mappt FFT-Magnituden (linear) auf logarithmisch verteilte Bänder (realistisch wie bei Kurzwellen/Spektrum)."""
    n = len(magnitudes)
    if n < 2 or num_bands < 1:
        return [0.0] * num_bands
    out = []
    for i in range(num_bands):
        start = int(n ** (i / num_bands))
        end = min(n, int(n ** ((i + 1) / num_bands)) + 1)
        if start >= end:
            start = max(0, end - 1)
        band_max = float(np.max(magnitudes[start:end]))
        out.append(band_max)
    if out:
        peak = max(out) or 1.0
        return [min(100.0, 100.0 * (v / peak) ** 0.6) for v in out]
    return [0.0] * num_bands


class SpectrumBandWidget(QWidget):
    """Frequenzbandanzeige: unten Grün, darüber Gelb, oben Rot; mit Peak Hold."""

    def __init__(self, parent=None, num_bands: int = 8):
        super().__init__(parent)
        self._bands = [0.0] * num_bands
        self._peak_hold = [0.0] * num_bands
        self._num_bands = num_bands
        self._peak_hold_decay = 0.99
        self.setMinimumSize(120, 48)
        self.setStyleSheet("background: #0a0a0a; border: none;")

    def set_bands(self, values: List[float]):
        self._bands = list(values)[: self._num_bands]
        if len(self._bands) < self._num_bands:
            self._bands.extend([0.0] * (self._num_bands - len(self._bands)))
        for i, v in enumerate(self._bands):
            if i < len(self._peak_hold):
                self._peak_hold[i] = max(self._peak_hold[i] * self._peak_hold_decay, v)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        w, h = self.width(), self.height()
        if w < 4 or h < 4:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 2
        bar_w = max(2, (w - margin * 2 - (self._num_bands - 1) * 2) // self._num_bands)
        gap = 2
        x = margin
        draw_h = h - margin * 2
        for i, val in enumerate(self._bands):
            pct = max(0.0, min(1.0, val / 100.0))
            bar_h = int(draw_h * pct)
            if bar_h > 0:
                y_bottom = h - margin
                y_top = y_bottom - bar_h
                green_h = int(draw_h * min(pct, 0.65))
                yellow_h = int(draw_h * max(0, min(pct, 0.85) - 0.65))
                red_h = int(draw_h * max(0, pct - 0.85))
                if green_h > 0:
                    painter.fillRect(int(x), y_bottom - green_h, bar_w, green_h, QColor("#22c55e"))
                if yellow_h > 0:
                    painter.fillRect(int(x), y_bottom - green_h - yellow_h, bar_w, yellow_h, QColor("#eab308"))
                if red_h > 0:
                    painter.fillRect(int(x), y_bottom - green_h - yellow_h - red_h, bar_w, red_h, QColor("#dc2626"))
            ph = max(0.0, min(1.0, (self._peak_hold[i] if i < len(self._peak_hold) else 0) / 100.0))
            if ph > 0.02:
                peak_y = h - margin - int(draw_h * ph)
                painter.setPen(QPen(QColor("#94a3b8"), 1))
                painter.drawLine(int(x), peak_y, int(x + bar_w), peak_y)
            x += bar_w + gap
        painter.end()


class WaveformWidget(QWidget):
    """Wellenform-Anzeige (Oszilloskop-Stil, realistisch): Mittellinie = 0, geglättete Kurve."""

    def __init__(self, parent=None, max_points: int = 80):
        super().__init__(parent)
        self._points: deque = deque(maxlen=max_points)
        self.setMinimumSize(120, 40)
        self.setStyleSheet("background: #0a0a0a; border: none;")

    def append(self, value: float):
        self._points.append(max(0, min(100, value)))
        self.update()

    def _smooth(self, pts: List[float], window: int = 3) -> List[float]:
        if len(pts) < window:
            return pts
        out = []
        for i in range(len(pts)):
            start = max(0, i - window // 2)
            end = min(len(pts), i + window // 2 + 1)
            out.append(sum(pts[start:end]) / (end - start))
        return out

    def paintEvent(self, event):
        super().paintEvent(event)
        w, h = self.width(), self.height()
        if w < 4 or h < 4 or len(self._points) < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 4
        draw_w = w - margin * 2
        draw_h = h - margin * 2
        # Null unten: y_bottom = margin + draw_h, Amplitude 0..100 → Höhe nach oben
        y_bottom = margin + draw_h
        # Oszilloskop-Gitter: Zeit- und Amplituden-Raster (Null-Linie unten)
        grid_color = QColor("#1e293b")
        painter.setPen(QPen(grid_color, 1))
        for i in range(1, 5):
            x = margin + (i * draw_w / 5)
            painter.drawLine(int(x), margin, int(x), margin + draw_h)
        for i in range(1, 4):
            y = margin + (i * draw_h / 4)
            painter.drawLine(margin, int(y), margin + draw_w, int(y))
        painter.drawRect(margin, margin, int(draw_w), int(draw_h))
        pts = list(self._points)
        pts = self._smooth(pts, 3)
        n = len(pts)
        path = QPainterPath()
        fill_path = QPainterPath()
        fill_path.moveTo(margin, y_bottom)
        for i, val in enumerate(pts):
            x = margin + (i / max(1, n - 1)) * draw_w
            # val 0..100: 0 = unten (y_bottom), 100 = oben (margin)
            pct = max(0.0, min(1.0, val / 100.0))
            y = y_bottom - pct * draw_h
            y = max(margin, min(y_bottom, y))
            if i == 0:
                path.moveTo(x, y)
                fill_path.lineTo(x, y)
            else:
                path.lineTo(x, y)
                fill_path.lineTo(x, y)
        fill_path.lineTo(margin + draw_w, y_bottom)
        fill_path.closeSubpath()
        painter.fillPath(fill_path, QColor(34, 197, 94, 35))
        painter.setPen(QPen(QColor("#22c55e"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.setPen(QPen(QColor("#475569"), 1))
        painter.drawLine(int(margin), int(y_bottom), int(margin + draw_w), int(y_bottom))
        painter.end()


class StationListDialog(QDialog):
    """Senderliste aus radio-browser.info: nur Sendername (keine URL), Checkbox = Favorit an/ab."""

    def __init__(self, parent: Optional[QMainWindow], current_favorites: List[Dict[str, Any]], theme_name: str = "Klavierlack"):
        super().__init__(parent)
        self.setWindowTitle("Senderliste – Favoriten (radio-browser.info)")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(THEMES.get(theme_name, STYLE_KLAVIERLACK))
        self._current_favorites = list(current_favorites)
        self._add_station = None
        self._rebuild_favorite_urls_set()
        layout = QVBoxLayout(self)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Sender suchen (z. B. 1Live, NDR, SAW…)")
        self._search.setMinimumHeight(44)
        layout.addWidget(self._search)
        search_btn = QPushButton("Suchen")
        search_btn.setMinimumHeight(48)
        search_btn.clicked.connect(self._do_search)
        self._search.returnPressed.connect(self._do_search)
        layout.addWidget(search_btn)
        self._list = QListWidget()
        self._list.setMinimumHeight(280)
        self._list.setIconSize(QSize(28, 28))
        self._list.itemChanged.connect(self._on_item_check_changed)
        layout.addWidget(self._list)
        layout.addWidget(QLabel("☑ = Favorit (max. 64). Keine URL-Anzeige."))
        close_btn = QPushButton("Schließen")
        close_btn.setMinimumHeight(48)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        # Sofort Minimal-Liste anzeigen, damit nie eine leere Liste erscheint
        self._fill_list_immediate()
        self._do_search()

    def _rebuild_favorite_urls_set(self):
        """Baut _favorite_urls aus Favoriten-URLs plus kanonische RADIO_STATIONS-URLs (für Haken bei Senderliste aus stations.py)."""
        urls = set()
        for f in self._current_favorites:
            u = _normalize_favorite_url(f.get("stream_url") or f.get("url") or "")
            if u:
                urls.add(u)
            name = (f.get("name") or "").strip()
            if name:
                for s in RADIO_STATIONS:
                    if (s.get("name") or "").strip() == name:
                        alt = _normalize_favorite_url(s.get("stream_url") or s.get("url") or "")
                        if alt:
                            urls.add(alt)
                        break
        self._favorite_urls = urls

    def _fill_list_immediate(self):
        """Zeigt sofort eine Senderliste (RADIO_STATIONS oder Minimal), damit nie nur 5 erscheinen."""
        list_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
        minimal = [
            {"name": "1Live", "url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "favicon": "", "state": "NRW", "tags": "Pop"},
            {"name": "WDR 2", "url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "favicon": "", "state": "NRW", "tags": "Pop"},
            {"name": "Deutschlandfunk", "url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "favicon": "", "state": "Bundesweit", "tags": "Info"},
            {"name": "R.SA", "url": "http://streams.rsa-sachsen.de/rsa-live/mp3-192/rsamediaplayer", "favicon": "", "state": "Sachsen", "tags": "Pop"},
            {"name": "Radio SAW", "url": "https://stream.radiosaw.de/saw/mp3-192/radio-browser/", "favicon": "", "state": "Sachsen-Anhalt", "tags": "Pop"},
        ]
        # Wenn RADIO_STATIONS viele Einträge hat (z. B. aus stations.py), diese anzeigen
        raw = list(RADIO_STATIONS)[:50] if RADIO_STATIONS else minimal
        if len(raw) < 10:
            raw = minimal
        sources = []
        for s in raw:
            if not isinstance(s, dict):
                continue
            url = (s.get("url") or s.get("stream_url") or "").strip()
            sources.append({
                "name": (s.get("name") or "?").strip(),
                "url": url,
                "favicon": (s.get("favicon") or s.get("logo_url") or "").strip(),
                "state": (s.get("state") or s.get("region") or "").strip(),
                "tags": (s.get("tags") or s.get("genre") or "").strip(),
            })
        if not sources:
            sources = minimal
        try:
            self._list.itemChanged.disconnect(self._on_item_check_changed)
        except Exception:
            pass
        self._list.clear()
        for s in sources:
            if not isinstance(s, dict):
                continue
            name = (s.get("name") or "?").strip()
            url = (s.get("url") or s.get("stream_url") or "").strip()
            st = {"name": name, "url": url, "favicon": s.get("favicon") or s.get("logo_url") or "", "state": s.get("state") or s.get("region") or "", "tags": s.get("tags") or s.get("genre") or ""}
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, st)
            item.setFlags(list_flags)
            item.setCheckState(Qt.CheckState.Checked if _normalize_favorite_url(url) in self._favorite_urls else Qt.CheckState.Unchecked)
            self._list.addItem(item)
        try:
            self._list.itemChanged.connect(self._on_item_check_changed)
        except Exception:
            pass

    def _station_to_fav(self, s: dict) -> dict:
        url = (s.get("url") or s.get("stream_url") or "").strip()
        return {
            "id": "rb_" + str(hash(url) % 10**8),
            "name": (s.get("name") or "?").strip(),
            "stream_url": url,
            "logo_url": (s.get("favicon") or "").strip() or "",
            "region": s.get("state") or "",
            "genre": s.get("tags") or "",
        }

    def _on_item_check_changed(self, item: QListWidgetItem):
        if not item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            return
        s = item.data(Qt.ItemDataRole.UserRole)
        if not s or not isinstance(s, dict):
            return
        url = (s.get("url") or s.get("stream_url") or "").strip()
        if not url:
            return
        checked = item.checkState() == Qt.CheckState.Checked
        self._rebuild_favorite_urls_set()
        if checked:
            if _normalize_favorite_url(url) in self._favorite_urls:
                return
            if len(self._current_favorites) >= FAVORITES_MAX:
                QMessageBox.information(self, "Favoriten", f"Maximal {FAVORITES_MAX} Sender.")
                item.setCheckState(Qt.CheckState.Unchecked)
                return
            fav = self._station_to_fav(s)
            self._current_favorites.append(fav)
            self._add_station = fav
        else:
            norm = _normalize_favorite_url(url)
            self._current_favorites = [f for f in self._current_favorites if _normalize_favorite_url(f.get("stream_url") or f.get("url") or "") != norm]
        save_favorites(self._current_favorites)
        if self.parent():
            self.parent()._reload_favorites()
            if hasattr(self.parent(), "_rebuild_station_buttons"):
                self.parent()._rebuild_station_buttons()

    def _do_search(self):
        name = self._search.text().strip()

        def do():
            stations_result = []
            try:
                stations_result = _fetch_stations_search(name)
                if not isinstance(stations_result, list):
                    stations_result = []
            except Exception:
                pass
            # Werte für Hauptthread-Update (Lambda könnte verzögert laufen)
            stations_copy = list(stations_result) if stations_result else []
            search_name_copy = str(name)

            def apply():
                list_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
                minimal = [
                    {"name": "1Live", "url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "favicon": "", "state": "NRW", "tags": "Pop"},
                    {"name": "WDR 2", "url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "favicon": "", "state": "NRW", "tags": "Pop"},
                    {"name": "Deutschlandfunk", "url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "favicon": "", "state": "Bundesweit", "tags": "Info"},
                    {"name": "R.SA", "url": "http://streams.rsa-sachsen.de/rsa-live/mp3-192/rsamediaplayer", "favicon": "", "state": "Sachsen", "tags": "Pop"},
                    {"name": "Radio SAW", "url": "https://stream.radiosaw.de/saw/mp3-192/radio-browser/", "favicon": "", "state": "Sachsen-Anhalt", "tags": "Pop"},
                ]

                def add_minimal():
                    for s in minimal:
                        item = QListWidgetItem(s["name"])
                        item.setData(Qt.ItemDataRole.UserRole, s)
                        item.setFlags(list_flags)
                        item.setCheckState(Qt.CheckState.Checked if _normalize_favorite_url(s.get("url") or "") in self._favorite_urls else Qt.CheckState.Unchecked)
                        self._list.addItem(item)

                try:
                    self._list.itemChanged.disconnect(self._on_item_check_changed)
                except Exception:
                    pass
                self._list.clear()
                self._rebuild_favorite_urls_set()

                def matches(s: dict, q: str) -> bool:
                    if not q:
                        return True
                    # Leerzeichen ignorieren, damit "1 Live" auch "1Live" findet
                    n = (s.get("name") or "").lower().replace(" ", "")
                    qn = q.strip().lower().replace(" ", "")
                    return qn in n

                # Immer Modul-Variable nutzen; Fallback nie leer (RADIO_STATIONS oder Minimal-Liste)
                fallback = list(RADIO_STATIONS)[:50] if RADIO_STATIONS else []
                if not fallback:
                    fallback = [
                        {"name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
                        {"name": "WDR 2", "stream_url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
                        {"name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "logo_url": "", "region": "Bundesweit", "genre": "Info"},
                        {"name": "R.SA", "stream_url": "http://streams.rsa-sachsen.de/rsa-live/mp3-192/rsamediaplayer", "logo_url": "", "region": "Sachsen", "genre": "Pop"},
                        {"name": "Radio SAW", "stream_url": "https://stream.radiosaw.de/saw/mp3-192/radio-browser/", "logo_url": "", "region": "Sachsen-Anhalt", "genre": "Pop"},
                    ]
                q = search_name_copy.strip().lower()

                try:
                    if not stations_copy:
                        source = [s for s in fallback if matches(s, q)]
                        for s in source:
                            st = {"name": s.get("name"), "url": s.get("stream_url"), "favicon": s.get("logo_url"), "state": s.get("region"), "tags": s.get("genre")}
                            display_name = (s.get("name") or "?").strip()
                            item = QListWidgetItem(display_name)
                            item.setData(Qt.ItemDataRole.UserRole, st)
                            item.setFlags(list_flags)
                            item.setCheckState(Qt.CheckState.Checked if _normalize_favorite_url(st.get("url") or "") in self._favorite_urls else Qt.CheckState.Unchecked)
                            self._list.addItem(item)
                    else:
                        to_show = [s for s in stations_copy if isinstance(s, dict) and matches(s, q)] if q else stations_copy
                        for s in to_show:
                            if not isinstance(s, dict):
                                continue
                            station_name = (s.get("name") or "Unbekannt").strip()
                            url = (s.get("url") or s.get("stream_url") or "").strip()
                            item = QListWidgetItem(station_name)
                            item.setData(Qt.ItemDataRole.UserRole, s)
                            item.setFlags(list_flags)
                            item.setCheckState(Qt.CheckState.Checked if _normalize_favorite_url(url) in self._favorite_urls else Qt.CheckState.Unchecked)
                            self._list.addItem(item)
                except Exception:
                    pass
                if self._list.count() == 0:
                    add_minimal()

                # Sortierung: Favoriten zuerst (alphabetisch), dann Rest (alphabetisch)
                self._sort_list_favorites_first()
                try:
                    self._list.itemChanged.connect(self._on_item_check_changed)
                except Exception:
                    pass
                # Icons (Favicons) asynchron nachladen
                QTimer.singleShot(100, self._load_station_icons)

            QTimer.singleShot(0, apply)
        threading.Thread(target=do, daemon=True).start()

    def _sort_list_favorites_first(self):
        """Liste so sortieren: zuerst Favoriten (alphabetisch), dann Rest (alphabetisch)."""
        try:
            self._list.itemChanged.disconnect(self._on_item_check_changed)
        except Exception:
            pass
        items_data = []
        for row in range(self._list.count()):
            it = self._list.item(row)
            if it is None:
                continue
            name = (it.text() or "").strip()
            checked = it.checkState() == Qt.CheckState.Checked
            data = it.data(Qt.ItemDataRole.UserRole)
            items_data.append((0 if checked else 1, name.lower(), name, data, checked))
        items_data.sort(key=lambda x: (x[0], x[1]))
        self._list.clear()
        list_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
        for _order, _key, name, data, checked in items_data:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, data)
            item.setFlags(list_flags)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self._list.addItem(item)
        try:
            self._list.itemChanged.connect(self._on_item_check_changed)
        except Exception:
            pass

    def _set_icon_for_row(self, row: int, data: bytes):
        """Hauptthread: Icon für eine Zeile setzen (von Favicon-Daten)."""
        if row < 0 or row >= self._list.count():
            return
        item = self._list.item(row)
        if not item:
            return
        pix = QPixmap()
        if pix.loadFromData(data) and not pix.isNull():
            item.setIcon(QIcon(pix.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))

    def _load_station_icons(self):
        """Favicons für alle Sender in der Liste asynchron laden (Worker-Thread, UI-Updates im Hauptthread)."""
        for row in range(self._list.count()):
            item = self._list.item(row)
            if not item:
                continue
            s = item.data(Qt.ItemDataRole.UserRole)
            if not s or not isinstance(s, dict):
                continue
            favicon = (s.get("favicon") or s.get("logo_url") or "").strip()
            if not favicon:
                continue
            r = row

            def fetch_and_set(url: str, row_index: int):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "DSI-Radio/1.0"})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = resp.read()
                    if data:
                        QTimer.singleShot(0, lambda: self._set_icon_for_row(row_index, data))
                except Exception:
                    pass
            threading.Thread(target=fetch_and_set, args=(favicon, r), daemon=True).start()

    def get_added_station(self):
        return getattr(self, "_add_station", None)


class DraggableTitleBar(QFrame):
    """Titelleiste zum Verschieben des Frameless-Fensters per Maus."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self._drag_start is not None:
            win = self.window()
            if win:
                win.move(win.pos() + e.globalPosition().toPoint() - self._drag_start)
                self._drag_start = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None


class DsiRadioWindow(QMainWindow):
    # Signale für Timer-Start im Hauptthread (vermeidet QBasicTimer-Warnung bei Aufruf aus beliebigem Thread)
    _startClockTimerRequested = pyqtSignal()
    _startStreamTimersRequested = pyqtSignal()
    # Backend-LED: Signal aus Worker-Thread → Slot läuft im Hauptthread (Qt.AutoConnection)
    _backendStatusChanged = pyqtSignal(bool)
    # Metadaten aus Worker-Thread anwenden (Slot läuft garantiert im Hauptthread)
    _metadataApplyRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._startClockTimerRequested.connect(self.startClockTimerSlot)
        self._startStreamTimersRequested.connect(self.startStreamTimersSlot)
        self._backendStatusChanged.connect(self._set_backend_led)
        self._metadataApplyRequested.connect(self._apply_pending_metadata_slot)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._gst_player = gst_player.GstPlayer() if gst_player.is_available() else None
        self._gst_bus_timer = QTimer(self)
        self._gst_bus_timer.timeout.connect(self._gst_poll_bus)
        # Favorites und Theme lazy laden (nur wenn benötigt)
        self._favorites: List[Dict[str, Any]] = []
        self._current_station = {}
        self._playing = False
        self._metadata: dict = {}
        self._theme = "Klavierlack"  # Default-Theme, wird später geladen
        self._favorites_page = 0
        self._old_default_sink = None  # Speichert den ursprünglichen Standard-Sink
        self._metadata_timer = QTimer(self)
        self._metadata_timer.timeout.connect(self._poll_metadata)
        self._metadata_check_timer = QTimer(self)
        self._metadata_check_timer.timeout.connect(self._check_and_apply_metadata)
        self._pending_metadata = None
        self._pending_metadata_force_show = False
        self._pending_metadata_url = ""
        # Timer startet erst beim Stream-Start (nicht beim App-Start)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._vu_timer = QTimer(self)
        self._vu_timer.timeout.connect(self._update_vu)
        self._auto_start_done = False  # Beim ersten showEvent Sender Platz 1 starten
        self._unavailable_stream_urls: set = set()
        self._backend_ok = False  # für Backend-LED
        self._build_ui()
        # Backend-Status prüfen (LED grün/rot), alle 5 s – Start aus showEvent (zentraler Slot)
        self._backend_check_timer = QTimer(self)
        self._backend_check_timer.timeout.connect(self._check_backend_for_led)
        QTimer.singleShot(1500, self._check_backend_for_led)  # Erste Prüfung verzögert, damit Fenster schneller erscheint
        # Player, Favorites und Theme nach UI-Build laden (nicht-blockierend)
        QTimer.singleShot(0, self._load_data_async)

    def _load_data_async(self):
        """Lädt Favorites und Theme nach UI-Build; schwere Schritte verzögert, damit Fenster schnell erscheint."""
        self._favorites = load_favorites()
        self._theme = load_theme()
        last = load_last_station()
        last_url = (last or {}).get("stream_url") or (last or {}).get("url") or ""
        if last_url and self._favorites:
            for f in self._favorites:
                if ((f.get("stream_url") or f.get("url") or "").strip() == last_url.strip()):
                    self._current_station = f
                    if hasattr(self, "_station_label"):
                        self._station_label.setText(f.get("name", "—"))
                    if hasattr(self, "_show_label"):
                        self._show_label.setText("Es läuft:")
                    break
        if self._favorites and not self._current_station:
            self._current_station = self._favorites[0]
            if hasattr(self, "_station_label"):
                self._station_label.setText(self._current_station.get("name", "—"))
        # Schwere Schritte (Buttons, Logo, Display-Config) nach kurzer Verzögerung → Fenster erscheint zuerst
        QTimer.singleShot(5, self._deferred_after_load)

    def _deferred_after_load(self):
        """Nach Start: Sender-Buttons, Logo, Anzeige-Optionen (fenster war schon sichtbar)."""
        self._update_senderinfo()
        self._update_logo()
        self._rebuild_station_buttons()
        disp = load_display_config()
        if hasattr(self, "_clock_label"):
            self._clock_label.setVisible(disp.get("show_clock", True))
        if hasattr(self, "_vu_mode_slider"):
            self._vu_mode_slider.setValue(1 if disp.get("vu_mode") == "analog" else 0)
            self._on_vu_slider(self._vu_mode_slider.value())
        QTimer.singleShot(2000, lambda: threading.Thread(target=self._background_station_update, daemon=True).start())

    def _reload_favorites(self):
        self._favorites = load_favorites()
        if self._favorites and not any(s.get("id") == self._current_station.get("id") for s in self._favorites):
            self._current_station = self._favorites[0]

    def _check_backend_for_led(self):
        """Prüft im Hintergrund ob Backend erreichbar ist und setzt LED (grün/rot) im Hauptthread.
        Probiert zuerst 127.0.0.1:8000 (Service), dann BACKEND_BASE. Jede 2xx-Antwort = erreichbar."""
        def _log(msg: str) -> None:
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(os.path.join(CONFIG_DIR, "backend_led_check.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} {msg}\n")
            except Exception:
                pass

        def _try(url: str, timeout: float = 5.0) -> bool:
            try:
                base = url.rstrip("/")
                if not base.startswith("http"):
                    base = "http://" + base
                req = urllib.request.Request(
                    base + "/api/version",
                    headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    code = getattr(resp, "status", getattr(resp, "code", 0))
                    if 200 <= code < 300:
                        try:
                            data = json.loads(resp.read().decode())
                            if isinstance(data, dict) and data.get("status") == "success":
                                return True
                        except Exception:
                            pass
                        return True  # 2xx reicht
                    return False
            except Exception as e:
                _log(f"Versuch {url!r}: {type(e).__name__}: {e}")
                return False

        def do():
            global BACKEND_BASE
            fallback_url = "http://127.0.0.1:8000"
            ok = _try(fallback_url)
            if ok:
                BACKEND_BASE = fallback_url
                _log("Backend erreichbar (127.0.0.1:8000) -> LED grün")
            else:
                ok = _try(BACKEND_BASE)
                _log(f"Backend-Check: ok={ok} (nach 127.0.0.1 und BACKEND_BASE)")
            # Signal-Emission aus Thread: Slot _set_backend_led läuft im Hauptthread (LED-Update)
            self._backendStatusChanged.emit(ok)

        threading.Thread(target=do, daemon=True).start()

    def _set_backend_led(self, ok: bool):
        """Setzt die runde Backend-LED: grün = erreichbar, rot = nicht erreichbar (läuft im Hauptthread)."""
        if not getattr(self, "_backend_led", None):
            return
        self._backend_ok = ok
        color = "#16a34a" if ok else "#dc2626"  # grün / rot
        self._backend_led.setStyleSheet(
            f"QLabel#backendLed {{ background-color: {color}; border-radius: 7px; border: 1px solid #c0c0c0; }}"
        )

    def _check_stream_reachable(self, url: str, timeout: float = 3.0) -> bool:
        """Prüft ob Stream-URL erreichbar ist (HEAD/GET)."""
        if not (url or "").strip().startswith(("http://", "https://")):
            return False
        try:
            req = urllib.request.Request(url.strip(), headers={"User-Agent": "PI-Installer-DSI-Radio/1.0", "Icy-MetaData": "1"})
            req.get_method = lambda: "HEAD"
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= getattr(resp, "status", 200) < 400
        except Exception:
            try:
                req = urllib.request.Request(url.strip(), headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return True
            except Exception:
                return False

    def _background_station_update(self):
        """Einmal pro Start: Favoriten-Streams prüfen, nicht erreichbare markieren; Radio-Browser-Cache aufwärmen."""
        unavailable = set()
        for s in getattr(self, "_favorites", []):
            url = (s.get("stream_url") or s.get("url") or "").strip()
            if url and not self._check_stream_reachable(url):
                unavailable.add(url)
        if unavailable:
            def apply():
                self._unavailable_stream_urls |= unavailable
                self._rebuild_station_buttons()
            QTimer.singleShot(0, apply)
        # Radio-Browser-API einmal anfragen (Aktualität, Cache für Senderliste/Suche)
        try:
            req = urllib.request.Request(
                f"{BACKEND_BASE}/api/radio/stations/search?country=Germany&limit=50",
                headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"}
            )
            urllib.request.urlopen(req, timeout=8)
        except Exception:
            pass

    def _build_ui(self):
        self._apply_theme(self._theme)
        # Portrait Standard (DSI 480×800); bei Start ohne Skript trotzdem Portrait
        portrait = os.environ.get("PI_INSTALLER_DSI_PORTRAIT", "1").lower() in ("1", "true", "yes")
        screen = QApplication.primaryScreen()
        is_desktop = bool(screen and screen.availableGeometry().width() >= 800 and screen.availableGeometry().height() >= 640)
        disp_cfg = load_display_config()
        display_max_width = disp_cfg.get("display_max_width", 600)
        display_font_scale = disp_cfg.get("display_font_scale", 0.85)
        self._is_desktop = is_desktop
        central = QWidget()
        central.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1e293b, stop:0.3 #0f172a, stop:0.7 #1e293b, stop:1 #334155);
            border: 1px solid #475569;
            border-radius: 16px;
        """)
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        central.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(8, 8, 8, 10)
        main_v.setSpacing(6)

        # Titelleiste: App-Name größer, Untertitel darunter kleiner; ziehbar → Fenster verschieben
        top_bar = DraggableTitleBar()
        top_bar.setStyleSheet("background: #0a0a0a; border: none; padding: 2px 6px;")
        top_bar.setFixedHeight(48)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(8, 2, 6, 2)
        top_bar_layout.setSpacing(8)
        title_block = QWidget()
        title_block.setStyleSheet("background: transparent; border: none;")
        title_block_layout = QVBoxLayout(title_block)
        title_block_layout.setContentsMargins(0, 6, 0, 0)
        title_block_layout.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(4)
        self._title_label_bar = QLabel("Sabrina Tuner")
        self._title_label_bar.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self._title_label_bar.setStyleSheet("color: #e2e8f0; border: none; background: transparent;")
        self._title_label_bar.setMinimumHeight(20)
        title_row.addWidget(self._title_label_bar)
        self._valentine_heart = QLabel("❤")
        self._valentine_heart.setStyleSheet("color: #dc2626; font-size: 22px; border: none; background: transparent;")
        self._valentine_heart.setVisible(datetime.now().month == 2 and datetime.now().day == 14)
        title_row.addWidget(self._valentine_heart, 0, Qt.AlignmentFlag.AlignVCenter)
        title_block_layout.addLayout(title_row)
        self._subtitle_label_bar = QLabel("VU-Meter + Titel/Interpret")
        self._subtitle_label_bar.setFont(QFont("Sans", 9))
        self._subtitle_label_bar.setStyleSheet("color: #94a3b8; border: none; background: transparent;")
        self._subtitle_label_bar.setMinimumHeight(14)
        title_block_layout.addWidget(self._subtitle_label_bar)
        top_bar_layout.addWidget(title_block, 0, Qt.AlignmentFlag.AlignVCenter)
        top_bar_layout.addStretch(1)
        clock_font = QFont("Sans", 12, QFont.Weight.Bold)
        self._clock_label = QLabel()
        self._clock_label.setFont(clock_font)
        self._clock_label.setStyleSheet("color: #94a3b8; border: none;")
        self._clock_label.setMinimumWidth(120)
        self._clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(self._clock_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_bar_layout.addStretch(1)
        # Backend-LED mit silbernem Kreis
        self._backend_led = QLabel()
        self._backend_led.setObjectName("backendLed")
        self._backend_led.setFixedSize(14, 14)
        self._backend_led.setToolTip("Backend-Status: Grün = erreichbar, Rot = nicht erreichbar")
        self._backend_led.setStyleSheet(
            "QLabel#backendLed { background-color: #dc2626; border-radius: 7px; border: 1px solid #c0c0c0; }"
        )
        top_bar_layout.addWidget(self._backend_led, 0, Qt.AlignmentFlag.AlignVCenter)
        # Minimize-Button (Größe wie Backend-LED: 14×14)
        self._min_btn = QPushButton("−")
        self._min_btn.setFixedSize(14, 14)
        self._min_btn.setToolTip("Minimieren")
        self._min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._min_btn.setStyleSheet("QPushButton { background: #334155; color: #e2e8f0; border: 1px solid #475569; border-radius: 3px; font-size: 10px; font-weight: bold; padding: 0; min-width: 14px; max-width: 14px; min-height: 14px; max-height: 14px; } QPushButton:hover { background: #475569; }")
        self._min_btn.clicked.connect(self.showMinimized)
        top_bar_layout.addWidget(self._min_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        # Maximize-Button (Größe wie Backend-LED: 14×14)
        self._max_btn = QPushButton("□")
        self._max_btn.setFixedSize(14, 14)
        self._max_btn.setToolTip("Vergrößern / Wiederherstellen")
        self._max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._max_btn.setStyleSheet("QPushButton { background: #334155; color: #e2e8f0; border: 1px solid #475569; border-radius: 3px; font-size: 9px; padding: 0; min-width: 14px; max-width: 14px; min-height: 14px; max-height: 14px; } QPushButton:hover { background: #475569; }")
        self._max_btn.clicked.connect(self._toggle_maximized)
        top_bar_layout.addWidget(self._max_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        # Ausschalter: deutlich kleiner, runder Metall-Button mit Power-Symbol
        self._close_btn = QPushButton("⏻")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setToolTip("Radio beenden (Ausschalter)")
        self._close_btn.clicked.connect(self.close)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e2e8f0, stop:0.5 #64748b, stop:1 #475569);
                color: #1e293b; font-weight: bold; font-size: 10px;
                border: 1px solid #94a3b8; border-radius: 10px;
                min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f1f5f9, stop:0.5 #cbd5e1, stop:1 #94a3b8); }
            QPushButton:pressed { background: #64748b; }
        """)
        top_bar_layout.addWidget(self._close_btn, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        main_v.addWidget(top_bar)

        # Radioanzeige: vollständige Breite, kein Abstand nach oben
        card = QFrame()
        card.setObjectName("display")
        card.setStyleSheet("background: transparent; border: none;")
        
        # Display-Container ohne Rahmen (Rahmen um Anzeigeinstrumente entfernt)
        black_frame = QFrame()
        black_frame.setStyleSheet("background: transparent; border: none; padding: 0;")
        black_frame_layout = QVBoxLayout(black_frame)
        black_frame_layout.setContentsMargins(0, 0, 0, 0)
        black_frame_layout.setSpacing(0)
        
        # Weißes Display (max. Breite aus Einstellungen, Standard 600 px)
        green_display = QFrame()
        green_display.setStyleSheet("""
            background: #ffffff;
            border: 1px solid #94a3b8;
            border-radius: 8px;
            padding: 4px;
        """)
        # Desktop: Display maximal 480 px Höhe, 640 px Breite; DSI/Portrait unverändert
        display_height = 480 if is_desktop else (292 + 200 + 80)
        green_display.setFixedHeight(display_height)
        green_display.setMaximumHeight(480)
        if is_desktop:
            green_display.setMaximumWidth(640)
        self._radio_display_frame = green_display
        logo_base = 120 if portrait else 130  # Größeres Logo (z. B. Energy gut lesbar)
        self._radio_display_logo_width = logo_base
        green_display_layout = QVBoxLayout(green_display)
        green_display_layout.setContentsMargins(3, 0, 3, 3)
        green_display_layout.setSpacing(0)
        # Test: Breite/Höhe oben rechts im Display
        self._display_size_label = QLabel()
        self._display_size_label.setStyleSheet("color: #64748b; font-size: 9px; border: none; background: transparent;")
        self._display_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        display_top_row = QHBoxLayout()
        display_top_row.setContentsMargins(0, 0, 0, 2)
        display_top_row.addStretch(1)
        display_top_row.addWidget(self._display_size_label, 0)
        green_display_layout.addLayout(display_top_row, 0)
        
        # Hauptbereich: Logo links, Text rechts (geringer Abstand zwischen Logo und Sendername/Titel)
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(2)
        
        # Logo-Bereich: 10 % größer
        logo_container = QVBoxLayout()
        logo_container.setSpacing(2)
        self._logo_label = QLabel()
        logo_max = self._radio_display_logo_width  # 94 (Portrait) bzw. 107 (Landscape)
        self._logo_label.setFixedSize(logo_max, logo_max)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("background-color: transparent; border: none; color: #0f172a; font-size: 20px;")
        self._logo_label.setText("…")
        self._logo_label.setScaledContents(False)  # Pixmap in Code proportional skalieren, keine Streckung
        logo_container.addWidget(self._logo_label)
        # Audioqualität unter Logo (fester Platz)
        self._quality_label = QLabel("")
        self._quality_label.setFont(QFont("Sans", 11))
        self._quality_label.setStyleSheet("color: #0f172a; border: none;")
        self._quality_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._quality_label.setMinimumHeight(18)
        self._quality_label.setMaximumHeight(24)
        logo_container.addWidget(self._quality_label)
        logo_container.addStretch()
        content_row.addLayout(logo_container, 0)
        
        # Text-Bereich rechts: Sendername, Musikrichtung, Titel, Interpret, Sendung
        text_container = QVBoxLayout()
        text_container.setSpacing(3)
        text_container.setContentsMargins(0, 0, 0, 0)
        
        self._display_font_scale = display_font_scale
        self._station_label = QLabel(self._current_station.get("name", "—"))
        base_station = max(10, int(22 * display_font_scale))
        self._station_label.setFont(QFont("Sans", base_station, QFont.Weight.Bold))
        self._station_label.setStyleSheet("color: #0f172a; border: none;")
        self._station_label.setMinimumHeight(34)
        self._station_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        text_container.addWidget(self._station_label)
        
        # Musikrichtung / Bereich (z. B. Sachsen-Anhalt, 70er)
        self._genre_label = QLabel(self._current_station.get("genre", ""))
        self._genre_label.setFont(QFont("Sans", max(9, int(14 * display_font_scale))))
        self._genre_label.setStyleSheet("color: #0f172a; border: none;")
        text_container.addWidget(self._genre_label)
        
        # Laufende Sendung / Moderator („Es läuft:“ + Inhalt – nicht abschneiden)
        self._show_label = QLabel("")
        self._show_label.setFont(QFont("Sans", max(9, int(12 * display_font_scale))))
        self._show_label.setStyleSheet("color: #0f172a; border: none;")
        self._show_label.setWordWrap(True)
        self._show_label.setMinimumHeight(38)
        self._show_label.setMaximumHeight(150)
        self._show_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        text_container.addWidget(self._show_label)
        
        # Titel (Liedtitel oder „Interpret – Titel“)
        self._title_label = QLabel("")
        self._title_label.setFont(QFont("Sans", max(10, int(14 * display_font_scale)), QFont.Weight.Bold))
        self._title_label.setStyleSheet("color: #0f172a; border: none;")
        self._title_label.setWordWrap(True)
        self._title_label.setMinimumHeight(28)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_container.addWidget(self._title_label)
        
        # Interpret
        self._artist_label = QLabel("")
        self._artist_label.setFont(QFont("Sans", max(10, int(14 * display_font_scale))))
        self._artist_label.setStyleSheet("color: #0f172a; border: none;")
        self._artist_label.setWordWrap(True)
        self._artist_label.setMinimumHeight(28)
        self._artist_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._artist_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_container.addWidget(self._artist_label)
        
        text_container.addStretch()
        content_row.addLayout(text_container, 1)
        
        # Basis-Schriftgrößen (mit Einstellung display_font_scale aus display.json)
        self._radio_display_font_sizes = {
            "station": max(10, int(22 * display_font_scale)),
            "genre": max(9, int(14 * display_font_scale)),
            "show": max(9, int(12 * display_font_scale)),
            "title": max(10, int(14 * display_font_scale)),
            "artist": max(10, int(14 * display_font_scale)),
        }
        green_display_layout.addLayout(content_row, 1)
        black_frame_layout.addWidget(green_display, 0)
        if is_desktop:
            black_frame.setMaximumHeight(480)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card_layout.addWidget(black_frame)
        card.setMaximumWidth(display_max_width)
        if is_desktop:
            card.setMaximumHeight(480)
            display_section = QWidget()
            display_section.setStyleSheet("background: transparent; border: none;")
            ds_layout = QVBoxLayout(display_section)
            ds_layout.setContentsMargins(0, 0, 0, 0)
            ds_layout.setSpacing(6)
            top_row = QWidget()
            top_row.setStyleSheet("background: transparent; border: none;")
            self._display_top_row_layout = QHBoxLayout(top_row)
            self._display_top_row_layout.setContentsMargins(0, 0, 0, 0)
            self._display_top_row_layout.setSpacing(8)
            # Reihenfolge: Display links, LED-Anzeige rechts daneben
            self._display_top_row_layout.addWidget(card, 1)
            ds_layout.addWidget(top_row)

        # Restliche UI-Elemente in horizontalem Layout
        main_h = QHBoxLayout()
        main_h.setSpacing(8)
        left = QWidget()
        left.setStyleSheet("background: transparent; border: none;")
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(left)
        layout.setSpacing(12 if portrait else 8)
        layout.setContentsMargins(0, 0, 0, 0)

        # VU L/R + Signal: kein Rahmen; Desktop: Höhe neben Display ausnutzen (größere LED-Strips)
        self._vu_mode = "led"
        self._vu_leds: List[List[QFrame]] = []
        self._vu_analog_widgets: List[AnalogGaugeWidget] = []
        vu_frame = QFrame()
        vu_frame.setStyleSheet("background: #0a0a0a; border: none; padding: 2px;")
        if is_desktop:
            vu_frame.setMinimumHeight(display_height)
            vu_frame.setMinimumWidth(90)
        vu_frame_layout = QHBoxLayout(vu_frame)
        # Oben 3–5 px Abstand; LED-Labels oben am Rand, 5 px darunter die Strips (max. Display-Höhe)
        margin_top = 4
        label_to_strip_gap = 5
        vu_frame_layout.setContentsMargins(2, margin_top, 2, 2)
        vu_frame_layout.setSpacing(16 if portrait else 8)
        vu_row = QHBoxLayout()
        vu_row.setSpacing(16 if portrait else 8)
        vu_row.setContentsMargins(0, 0, 0, 0)
        vu_row.addSpacing(5)
        led_container = QWidget()
        led_main = QVBoxLayout(led_container)
        led_main.setContentsMargins(0, 0, 0, 0)
        led_main.setSpacing(0)
        strip_height = (display_height - margin_top - 14 - label_to_strip_gap - 4) if is_desktop else 100  # Labels ~14px, 5px Abstand, 4px unten
        strip_height = max(80, strip_height)
        _vu_label_style = "color: #facc15; font-size: 10px; font-weight: bold; border: none; background: transparent;"
        # Zeile 1: L, R, Signal oben am Rand (Abstände wie bei Strips für Ausrichtung)
        labels_row = QHBoxLayout()
        labels_row.setContentsMargins(0, 0, 0, 0)
        labels_row.setSpacing(0)
        sp = 24 if is_desktop else 12
        for i, lab in enumerate(["L", "R", "Signal"]):
            if i == 1:
                labels_row.addSpacing(sp)
            elif i == 2:
                labels_row.addSpacing(sp * 2)
            lbl = QLabel(lab)
            lbl.setStyleSheet(_vu_label_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            labels_row.addWidget(lbl, 0, Qt.AlignmentFlag.AlignCenter)
        labels_row.addStretch(1)
        led_main.addLayout(labels_row)
        led_main.addSpacing(label_to_strip_gap)
        # Zeile 2: LED-Aussteuerung / Signalstärke (5 px unter den Labels)
        strips_row = QHBoxLayout()
        strips_row.setContentsMargins(0, 0, 0, 0)
        strips_row.setSpacing(0)
        for ch in range(3):
            if ch == 1:
                strips_row.addSpacing(sp)
            elif ch == 2:
                strips_row.addSpacing(sp * 2)
            strip = QWidget()
            strip.setFixedWidth(20 if is_desktop else 16)
            strip.setFixedHeight(strip_height)
            strip_layout = QVBoxLayout(strip)
            strip_layout.setContentsMargins(0, 0, 0, 0)
            strip_layout.setSpacing(1)
            frames = []
            seg_h = (strip_height - 9) // 10
            seg_h = max(6, min(seg_h, 28))
            for _ in range(10):
                f = QFrame()
                f.setFixedHeight(seg_h)
                f.setStyleSheet("background-color: #252525; border: none; border-radius: 1px;")
                frames.append(f)
            for idx in (9, 8, 7, 6, 5, 4, 3, 2, 1, 0):
                strip_layout.addWidget(frames[idx])
            self._vu_leds.append(frames)
            strips_row.addWidget(strip)
        strips_row.addStretch(1)
        led_main.addLayout(strips_row)
        vu_row.addWidget(led_container, 0)
        analog_container = QWidget()
        analog_layout = QHBoxLayout(analog_container)
        analog_layout.setContentsMargins(0, 0, 0, 0)
        analog_layout.setSpacing(0)
        gauge_sz = 80 if portrait else 64
        for ch, lab in enumerate(["L", "R", "Signal"]):
            if ch == 1:
                analog_layout.addSpacing(28 if portrait else 24)
            elif ch == 2:
                analog_layout.addSpacing(56 if portrait else 48)
            col = QVBoxLayout()
            lbl = QLabel(lab)
            lbl.setStyleSheet(_vu_label_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl, 0, Qt.AlignmentFlag.AlignHCenter)
            gauge = AnalogGaugeWidget(self, signal_mode=(ch == 2), size=gauge_sz)
            self._vu_analog_widgets.append(gauge)
            col.addWidget(gauge)
            analog_layout.addLayout(col)
        analog_layout.addStretch(1)
        analog_container.hide()
        vu_row.addWidget(analog_container, 0)
        self._vu_led_container = led_container
        self._vu_analog_container = analog_container
        vu_row.addStretch(1)
        # D/A-Schiebeschalter: kein Rahmen, D/A-Labels leuchtend gelb
        vu_switch = QWidget()
        vu_switch.setStyleSheet("background: transparent; border: none;")
        vu_switch_layout = QVBoxLayout(vu_switch)
        vu_switch_layout.setContentsMargins(0, 0, 0, 0)
        da_row = QHBoxLayout()
        da_row.setSpacing(4)
        da_lbl_style = "color: #facc15; font-size: 12px; font-weight: bold; background: transparent; border: none;"
        d_lbl = QLabel("D")
        d_lbl.setStyleSheet(da_lbl_style)
        d_lbl.setFixedWidth(16)
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        da_row.addWidget(d_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self._vu_mode_slider = QSlider(Qt.Orientation.Horizontal)
        self._vu_mode_slider.setMinimum(0)
        self._vu_mode_slider.setMaximum(1)
        self._vu_mode_slider.setValue(0)
        self._vu_mode_slider.setFixedWidth(50)
        self._vu_mode_slider.setFixedHeight(26)
        self._vu_mode_slider.setToolTip("D = Digital (LED), A = Analog")
        self._vu_mode_slider.valueChanged.connect(self._on_vu_slider)
        self._vu_mode_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1e293b, stop:0.5 #334155, stop:1 #1e293b);
                height: 14px;
                border-radius: 7px;
                border: 1px solid #0f172a;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e2e8f0, stop:0.3 #94a3b8, stop:0.5 #64748b, stop:0.7 #94a3b8, stop:1 #475569);
                width: 18px;
                height: 18px;
                margin: -2px 0;
                border-radius: 9px;
                border: 1px solid #94a3b8;
            }
            QSlider::handle:horizontal:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f1f5f9, stop:0.5 #cbd5e1, stop:1 #94a3b8); }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1e293b, stop:1 #334155);
                border-radius: 7px;
            }
            QSlider::add-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1e293b, stop:1 #334155);
                border-radius: 7px;
            }
        """)
        da_row.addWidget(self._vu_mode_slider, 0, Qt.AlignmentFlag.AlignCenter)
        a_lbl = QLabel("A")
        a_lbl.setStyleSheet(da_lbl_style)
        a_lbl.setFixedWidth(16)
        a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        da_row.addWidget(a_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        vu_switch_layout.addLayout(da_row)
        vu_row.addWidget(vu_switch, 0, Qt.AlignmentFlag.AlignBottom)
        vu_frame_layout.addLayout(vu_row)
        if is_desktop:
            self._display_top_row_layout.addWidget(vu_frame, 0)
            bottom_row = QWidget()
            bottom_row.setStyleSheet("background: transparent; border: none;")
            bottom_row_layout = QHBoxLayout(bottom_row)
            bottom_row_layout.setContentsMargins(0, 0, 0, 0)
            bottom_row_layout.setSpacing(6)
            self._spectrum_widget = SpectrumBandWidget(self, num_bands=24)
            self._spectrum_widget.setMinimumHeight(94)
            self._spectrum_widget.setToolTip("Frequenzbandanzeige (klassisch)")
            self._waveform_widget = WaveformWidget(self, max_points=80)
            self._waveform_widget.setMinimumHeight(94)
            self._waveform_widget.setToolTip("Wellenform (Oszilloskop-Stil)")
            bottom_row_layout.addWidget(self._spectrum_widget, 1)
            bottom_row_layout.addWidget(self._waveform_widget, 1)
            ds_layout.addWidget(bottom_row)
            main_v.addWidget(display_section)
            self._spectrum_bands = [0.0] * 24
            self._fft_buffer: deque = deque(maxlen=128)
        else:
            self._spectrum_widget = None
            self._waveform_widget = None
            self._spectrum_bands = [0.0] * 24
            self._fft_buffer = deque(maxlen=1)
        if not is_desktop:
            main_v.addWidget(card)
            layout.addWidget(vu_frame)

        # Sender-Buttons + rechts: Lautstärkeregler und Umschaltbutton als getrennte Komponenten
        self._btn_container = QWidget()
        self._btn_container.setStyleSheet("background: transparent; border: none;")
        self._btn_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._btn_layout = QGridLayout(self._btn_container)
        self._btn_layout.setSpacing(6)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._station_buttons: List[QPushButton] = []
        self._page_btn: Optional[QPushButton] = None
        page_row = QHBoxLayout()
        page_row.addWidget(self._btn_container, 1)
        # Seitenumschaltbutton 50 % größer, rechts neben die Senderbuttons
        page_btn_wrapper = QWidget()
        page_btn_wrapper.setStyleSheet("background: transparent; border: none;")
        page_btn_layout = QVBoxLayout(page_btn_wrapper)
        page_btn_layout.setContentsMargins(4, 0, 4, 0)
        page_btn_layout.setSpacing(0)
        self._page_btn = QPushButton(">")
        self._page_btn.setObjectName("pageSwitchBtn")
        self._page_btn.setFixedHeight(15)
        self._page_btn.setFixedWidth(12)
        self._page_btn.setToolTip("Seite wechseln")
        self._page_btn.setStyleSheet(
            "QPushButton#pageSwitchBtn { color: #fde047; font-size: 14px; font-weight: bold; background: #334155; border: 1px solid #64748b; border-radius: 1px; min-width: 12px; min-height: 15px; padding: 1px; line-height: 1; } "
            "QPushButton#pageSwitchBtn:hover { color: #fef08a; background: #475569; border-color: #94a3b8; } "
        )
        self._page_btn.clicked.connect(self._toggle_favorites_page)
        page_btn_layout.addWidget(self._page_btn, 0, Qt.AlignmentFlag.AlignCenter)
        page_row.addWidget(page_btn_wrapper, 0, Qt.AlignmentFlag.AlignBottom)
        page_row.addStretch(1)
        # Trennlinie, dann Lautstärkeregler weiter rechts
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background: #475569; max-width: 1px; border: none;")
        sep.setFixedWidth(1)
        page_row.addWidget(sep, 0, Qt.AlignmentFlag.AlignVCenter)
        vol_column = QWidget()
        vol_column.setStyleSheet("background: transparent; border: none; padding: 0;")
        vol_column.setFixedWidth(56)
        vol_column.setMinimumHeight(320)
        vol_layout = QVBoxLayout(vol_column)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.setSpacing(5)  # 5 px unter dem Lautstärkesymbol
        vol_lbl = QLabel("▶")
        vol_lbl.setStyleSheet("color: #facc15; font-size: 14px; font-weight: bold; border: none;")
        vol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_layout.addWidget(vol_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        self._volume_slider = QSlider(Qt.Orientation.Vertical)
        self._volume_slider.setMinimum(0)
        self._volume_slider.setMaximum(100)
        self._volume_slider.setValue(100)
        self._volume_slider.setMinimumHeight(220)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        self._volume_slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1e293b, stop:0.5 #334155, stop:1 #1e293b);
                width: 14px; border-radius: 7px; margin: 0 4px;
                border: 1px solid #0f172a;
                min-height: 220px;
            }
            QSlider::handle:vertical {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #e2e8f0, stop:0.3 #94a3b8, stop:0.5 #64748b, stop:0.7 #94a3b8, stop:1 #475569);
                height: 24px; width: 24px; margin: 0 -5px;
                border-radius: 12px;
                border: 1px solid #94a3b8;
            }
            QSlider::handle:vertical:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f1f5f9, stop:0.5 #cbd5e1, stop:1 #94a3b8); }
            QSlider::sub-page:vertical { background: #475569; border-radius: 7px; border: none; }
            QSlider::add-page:vertical { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1e293b, stop:1 #334155); border-radius: 7px; border: none; }
        """)
        vol_layout.addWidget(self._volume_slider, 1, Qt.AlignmentFlag.AlignCenter)
        page_row.addWidget(vol_column, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(page_row)
        self._rebuild_station_buttons()

        # Senderliste-Button: 22 px Höhe (4 px mehr als zuvor), ohne Rahmen
        self._list_btn = QPushButton("📻 Senderliste")
        self._list_btn.setToolTip("Senderliste öffnen")
        self._list_btn.setFixedHeight(22)
        self._list_btn.setMinimumWidth(120)
        self._list_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._list_btn.setObjectName("listBtn")
        self._list_btn.setStyleSheet(
            "QPushButton#listBtn { background-color: #334155; color: #e2e8f0; border: 1px solid #64748b; border-radius: 4px; padding: 0 8px; font-size: 11px; min-height: 22px; max-height: 22px; } "
            "QPushButton#listBtn:hover { background-color: #475569; border-color: #94a3b8; } "
        )
        self._list_btn.clicked.connect(self._open_station_list)
        layout.addWidget(self._list_btn)

        hint = QLabel("Kein Ton? Einstellungen → Sound → Ausgabegerät: Gehäuse-Lautsprecher.")
        hint.setStyleSheet("color: #64748b; font-size: 8px; border: none; background: transparent;")
        hint.setFixedHeight(20)
        hint.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(hint)
        
        # Audio-Ausgabegerät beim Start prüfen (reduzierte Verzögerung)
        QTimer.singleShot(50, self._check_audio_output)

        main_h.addWidget(left, 1)
        main_v.addLayout(main_h)
        # Größen-Griff zum Vergrößern/Verkleinern des Fensters
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 0, 0)
        grip_row.addStretch(1)
        size_grip = QSizeGrip(self)
        size_grip.setStyleSheet("QSizeGrip { background: #334155; border: 1px solid #475569; border-radius: 4px; width: 16px; height: 16px; }")
        size_grip.setToolTip("Fenster vergrößern/verkleinern")
        size_grip.setFixedSize(16, 16)
        grip_row.addWidget(size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        main_v.addLayout(grip_row)

        portrait = os.environ.get("PI_INSTALLER_DSI_PORTRAIT", "1").lower() in ("1", "true", "yes")
        # Desktop-Erkennung: großer Bildschirm (≥800×640) → Desktop-Größe, sonst DSI/Portrait
        screen = QApplication.primaryScreen()
        is_desktop = False
        if screen:
            geom = screen.availableGeometry()
            if geom.width() >= 800 and geom.height() >= 640:
                is_desktop = True
        if is_desktop:
            self.setMinimumSize(800, 640)
            self.resize(800, 640)
        elif portrait:
            self.setMinimumSize(480, 800)
            self.resize(480, 800)
        else:
            self.setMinimumSize(380, 320)
            self.resize(800, 480)
        self._update_logo()
        self._update_senderinfo()
        self._update_clock()
        self.setStyleSheet(self.styleSheet() + "\nQMainWindow { background-color: #0a0a0a; }")
        # Uhr- und Backend-Timer werden in showEvent per _startMainTimersSlot gestartet (500 ms Verzögerung)

    def _apply_theme(self, name: str):
        self._theme = name
        self.setStyleSheet(THEMES.get(name, STYLE_KLAVIERLACK))

    def _toggle_favorites_page(self):
        per_page = FAVORITES_PER_PAGE_DESKTOP if getattr(self, "_is_desktop", False) else FAVORITES_PER_PAGE
        total = len(self._favorites)
        if total <= per_page:
            return
        pages = (total + per_page - 1) // per_page
        self._favorites_page = (self._favorites_page + 1) % pages
        self._rebuild_station_buttons()

    def _rebuild_station_buttons(self):
        for b in self._station_buttons:
            b.deleteLater()
        self._station_buttons.clear()
        per_page = FAVORITES_PER_PAGE_DESKTOP if getattr(self, "_is_desktop", False) else FAVORITES_PER_PAGE
        # Spalten aus verfügbarer Breite: Buttons fließen in den freien Raum
        w = self._btn_container.width()
        cell = STATION_BTN_WIDTH + STATION_BTN_SPACING
        cols = max(1, min(16, w // cell)) if w > 0 else (4 if getattr(self, "_is_desktop", False) else 3)
        self._last_btn_cols = cols
        unavailable = getattr(self, "_unavailable_stream_urls", set())
        # Duplikate (URL + NDR 1/NDR 2 nur je einmal) entfernen
        unique_fav = _deduplicate_favorites_ndr(_deduplicate_favorites_by_url(self._favorites))
        if len(unique_fav) < len(self._favorites):
            self._favorites = unique_fav
            save_favorites(self._favorites)
        sorted_fav = sorted(self._favorites, key=lambda s: (s.get("name") or "").lower())
        pages = (len(sorted_fav) + per_page - 1) // per_page if sorted_fav else 1
        if self._favorites_page >= pages:
            self._favorites_page = max(0, pages - 1)
        start = self._favorites_page * per_page
        page_fav = sorted_fav[start : start + per_page]
        btn_style_normal = (
            "QPushButton { background-color: #334155; color: #e2e8f0; border: 1px solid #c0c0c0; border-radius: 6px; padding: 4px; font-size: 11px; } "
            "QPushButton:hover { background-color: #475569; } "
            "QPushButton:checked { background-color: #0d9488; color: white; border-color: #0f766e; }"
        )
        for i, s in enumerate(page_fav):
            url = (s.get("stream_url") or s.get("url") or "").strip()
            no_stream = url in unavailable
            label = "kein Stream" if no_stream else _button_label(s.get("name", "?"))
            b = QPushButton(label)
            b.setProperty("station_id", s.get("id"))
            b.setCheckable(True)
            b.setChecked(s.get("id") == self._current_station.get("id"))
            b.setFixedSize(80, 60)
            b.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if no_stream:
                b.setStyleSheet("QPushButton { background-color: #dc2626; color: white; font-weight: bold; border: 1px solid #c0c0c0; border-radius: 6px; padding: 4px; font-size: 11px; } QPushButton:checked { background-color: #b91c1c; }")
                b.setToolTip(f"{s.get('name', '?')}: Stream nicht erreichbar")
            else:
                b.setStyleSheet(btn_style_normal)
            b.clicked.connect(lambda checked=False, st=s: self._on_station(st))
            self._station_buttons.append(b)
            self._btn_layout.addWidget(b, i // cols, i % cols)
        if self._page_btn:
            total = len(self._favorites)
            self._page_btn.setVisible(total > per_page)
            pages = (total + per_page - 1) // per_page
            cur = self._favorites_page + 1
            self._page_btn.setToolTip("Seite %d/%d – klicken zum Wechseln" % (cur, pages))

    def _reflow_station_buttons_if_needed(self):
        """Prüft, ob sich die Spaltenzahl durch Containerbreite geändert hat; baut Buttons ggf. neu um."""
        w = self._btn_container.width()
        cell = STATION_BTN_WIDTH + STATION_BTN_SPACING
        new_cols = max(1, min(16, w // cell)) if w > 0 else 4
        if new_cols != getattr(self, "_last_btn_cols", 0):
            self._rebuild_station_buttons()

    def _open_station_list(self):
        dlg = StationListDialog(self, self._favorites, self._theme)
        dlg.exec()
        self._reload_favorites()
        self._rebuild_station_buttons()

    def _update_clock(self):
        self._clock_label.setText(datetime.now().strftime("%d.%m.%Y  %H:%M"))
        now = datetime.now()
        if getattr(self, "_valentine_heart", None) is not None:
            self._valentine_heart.setVisible(now.month == 2 and now.day == 14)

    def _toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_volume_changed(self, value: int):
        """Lautstärke des aktiven Kanals: PulseAudio/PipeWire oder ALSA setzen."""
        pct = max(0, min(100, value))
        pactl = _pactl_path()
        has_pulseaudio = pactl is not None
        
        if has_pulseaudio and pactl:
            try:
                r = subprocess.run(
                    [pactl, "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
                    timeout=2,
                    capture_output=True,
                    env=_pactl_env(),
                )
                if r.returncode == 0:
                    return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # ALSA Fallback (z. B. Raspberry Pi ohne PulseAudio)
        for args in (
            ["amixer", "-q", "set", "Master", f"{pct}%"],
            ["amixer", "-q", "-c", "0", "set", "PCM", f"{pct}%"],
            ["amixer", "-q", "-c", "0", "set", "Master", f"{pct}%"],
        ):
            try:
                result = subprocess.run(args, timeout=2, capture_output=True)
                if result.returncode == 0:
                    return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

    def _update_senderinfo(self):
        """Sendername bleibt; Bereich = Region und/oder Genre (z. B. Sachsen-Anhalt · Schlager)."""
        region = (self._current_station.get("region") or "").strip()
        genre = (self._current_station.get("genre") or "").strip()
        if region and genre:
            self._genre_label.setText(f"{region} · {genre}")
        else:
            self._genre_label.setText(region or genre)

    def _on_station(self, st: dict):
        self._current_station = st
        save_last_station(st)
        for b in self._station_buttons:
            b.setChecked(b.property("station_id") == st.get("id"))
        self._station_label.setText(st.get("name", "—"))
        self._update_senderinfo()
        self._title_label.setText("")
        self._artist_label.setText("")
        self._show_label.setText("Es läuft:")
        self._quality_label.setText("")
        self._metadata = {}
        QTimer.singleShot(0, self._update_radio_display_fonts)
        # Stopp sofort, Start und Logo im nächsten Event-Loop-Tick → UI bleibt reaktionsfähig
        self._stop_stream()
        QTimer.singleShot(10, lambda: (self._start_stream(), self._update_logo()))

    def _update_logo(self):
        """Logo anzeigen. Synchron laden (3s Timeout) für zuverlässige Anzeige und Screenshots."""
        station = self._current_station
        name = (station.get("name") or "?").strip()
        url = (station.get("logo_url") or "").strip()
        if not url:
            url = STATION_LOGO_FALLBACKS.get(name) or ""
        if not url:
            # Fallback: Teilweise Namensübereinstimmung (z. B. "Deutschlandfunk" enthält "DLF", "104.6 RTL" aus API)
            try:
                name_lower = name.lower()
                for s in RADIO_STATIONS:
                    sn = (s.get("name") or "").strip()
                    if not sn or not (s.get("logo_url") or "").strip():
                        continue
                    if sn == name or (name_lower in sn.lower() or sn.lower() in name_lower):
                        url = (s.get("logo_url") or "").strip()
                        break
                if not url:
                    for s in RADIO_STATIONS:
                        if (s.get("name") or "").strip() == name and (s.get("logo_url") or "").strip():
                            url = (s.get("logo_url") or "").strip()
                            break
            except Exception:
                pass
        self._logo_label.setPixmap(QPixmap())
        self._logo_label.setText(name[:2] if name else "…")
        if not url and not name:
            return
        data = _fetch_logo(url, name)
        if not data:
            return
        pix = QPixmap()
        pix.loadFromData(QByteArray(data))
        if pix.isNull():
            return
        # Logo nutzt die volle Box (größere Darstellung, z. B. Energy)
        box = self._logo_label.width() or 120
        box_h = self._logo_label.height() or 120
        max_w = max(48, box)
        max_h = max(48, box_h)
        ow, oh = pix.width(), pix.height()
        if ow > 0 and oh > 0:
            scale = min(max_w / ow, max_h / oh)
            new_w = int(ow * scale)
            new_h = int(oh * scale)
            scaled_pix = pix.scaled(new_w, new_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self._logo_label.setPixmap(scaled_pix)
        else:
            self._logo_label.setPixmap(pix)
        self._logo_label.setText("")

    def _gst_poll_bus(self):
        """GStreamer-Bus verarbeiten (EOS/ERROR/TAG). Stoppt Timer und setzt _playing bei Ende."""
        if not self._gst_player or not self._gst_player.is_active:
            return
        if not self._gst_player.poll_bus():
            self._gst_bus_timer.stop()
            self._playing = False
            for ch in (0, 1, 2):
                self._set_led_strip(ch, 0)

    def _start_stream(self):
        if not gst_player.is_available() or self._gst_player is None:
            gst_player.init()
            if not gst_player.is_available():
                self._title_label.setText("GStreamer nicht verfügbar")
                install_cmd = _INSTALL_SCRIPT if os.path.isfile(_INSTALL_SCRIPT) else "./scripts/install-dsi-radio-setup.sh"
                self._artist_label.setText("Terminal: sudo bash " + install_cmd)
                err = gst_player.get_availability_error() or "Unbekannt"
                self._show_label.setText(f"Grund: {err}. Danach App neu starten.")
                return
            self._gst_player = gst_player.GstPlayer()

        self._stop_stream()

        url = (self._current_station.get("stream_url") or self._current_station.get("url") or "").strip()
        url = _prefer_stations_py_stream_url(self._current_station, url)
        if not url:
            return

        audio_sink = _find_audio_sink()
        has_pulseaudio = _pactl_path() is not None
        force_sink_for_gstreamer = False  # Nur auf Freenove: expliziten Sink an GStreamer übergeben

        if not audio_sink:
            self._title_label.setText("Kein Audio-Ausgang gefunden!")
            self._artist_label.setText("Bitte Audio-Treiber aktivieren")
            try:
                with open(os.path.join(CONFIG_DIR, "stream_error.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: Stream nicht gestartet - kein Audio-Ausgang\n")
            except Exception:
                pass
            return

        # Standard-Sink setzen (GStreamer nutzt PulseAudio-Standard-Sink)
        if has_pulseaudio and audio_sink:
            pactl = _pactl_path()
            if pactl:
                try:
                    result = subprocess.run(
                        [pactl, "get-default-sink"],
                        capture_output=True, text=True, timeout=2, env=_pactl_env()
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        self._old_default_sink = result.stdout.strip()
                    is_freenove = False
                    try:
                        for bus in (1, 0, 6, 7):
                            r = subprocess.run(
                                ["i2cget", "-y", str(bus), "0x21", "0xfd"],
                                capture_output=True, timeout=0.2
                            )
                            if r.returncode == 0:
                                is_freenove = True
                                break
                    except Exception:
                        pass
                    if is_freenove and self._old_default_sink and "hdmi" in self._old_default_sink.lower():
                        audio_sink = self._old_default_sink
                    elif self._old_default_sink != audio_sink:
                        subprocess.run(
                            [pactl, "set-default-sink", audio_sink],
                            capture_output=True, text=True, timeout=2, env=_pactl_env()
                        )
                    if is_freenove:
                        force_sink_for_gstreamer = True  # Gehäuse-Lautsprecher explizit an Playbin übergeben
                except Exception:
                    pass

        try:
            def on_gst_error(err_str: str):
                err_lower = (err_str or "").lower()
                # Hinweis bei vermutlich fehlendem AAC/Codec-Decoder (z. B. NDR 1)
                hint_artist = ""
                hint_show = ""
                if any(x in err_lower for x in ("aac", "decode", "no element", "could not decode", "avdec")):
                    cmd = _INSTALL_SCRIPT if os.path.isfile(_INSTALL_SCRIPT) else "./scripts/install-dsi-radio-setup.sh"
                    hint_artist = "AAC/Codec: gstreamer1.0-libav installieren"
                    hint_show = "Terminal: sudo bash " + cmd
                def _apply():
                    self._title_label.setText("Streamfehler")
                    if hint_artist:
                        self._artist_label.setText(hint_artist)
                    if hint_show:
                        self._show_label.setText(hint_show)
                    self._playing = False
                QTimer.singleShot(0, _apply)

            def on_gst_tag(meta: dict):
                # GStreamer-Tags (ICY/Stream): title, artist, organization, stream-title usw.
                # Keys case-insensitive (GStreamer kann unterschiedliche Schreibweise nutzen)
                _m = {k.lower(): v for k, v in meta.items() if isinstance(v, str) and (v or "").strip()}
                def get(*keys):
                    for k in keys:
                        if k:
                            v = (_m.get(k.lower(), "") or "").strip()
                            if v:
                                return v
                    return ""
                title = get("title", "stream-title", "streamtitle", "icy-title") or ""
                if not title:
                    # Fallback: beliebiger Tag mit "Artist - Titel" (z. B. Radio SAW / streamABC, wie Lautstärkeregler)
                    for v in _m.values():
                        v = (v or "").strip()
                        if v and (" - " in v or " – " in v or "\u2013" in v):
                            title = v
                            break
                artist = get("artist") or ""
                song = get("song") or ""
                show = get("organization", "organization-name", "show") or ""
                # Kombinierten "Artist - Titel"-String in Artist/Song zerlegen (wie Lautstärkeregler/OSD)
                if title and not (artist or song) and (" - " in title or " – " in title or " \u2013 " in title):
                    for sep in (" - ", " – ", " \u2013 "):
                        if sep in title:
                            parts = title.split(sep, 1)
                            artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                            song = (parts[1].strip() or title) if len(parts) > 1 else title
                            break
                if not title and (artist or song):
                    title = f"{artist} - {song}".strip() if (artist and song) else (artist or song)
                applied = {"title": title, "artist": artist, "song": song, "show": show}
                if applied.get("title") or applied.get("artist") or applied.get("show"):
                    # poll_bus läuft im Hauptthread → UI direkt aktualisieren (wie Lautstärkeregler)
                    self._apply_metadata(applied, force_show=True)

            self._gst_player.set_callbacks(on_error=on_gst_error, on_tag=on_gst_tag)
            # Auf dem Laptop: kein Sink übergeben → GStreamer nutzt Standard-Ausgabe. Nur auf Freenove Sink erzwingen.
            self._gst_player.set_uri(url, pulse_sink_name=audio_sink if (has_pulseaudio and force_sink_for_gstreamer) else None)
            self._gst_player.play()

            self._playing = True
            station_name = (self._current_station or {}).get("name", "Livestream")
            self._title_label.setText(f"{station_name} – Live")
            self._show_label.setText("Es läuft:")
            self._vu_val_0 = 50
            self._vu_val_1 = 50
            # Timer kurz verzögert starten (Hauptthread-Event-Loop)
            QTimer.singleShot(100, self.startStreamTimersSlot)
            self._poll_metadata()
            QTimer.singleShot(300, self._poll_metadata)  # Früher nach Start für Titel/Interpret

            try:
                with open(os.path.join(CONFIG_DIR, "audio_sink.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: GStreamer playbin url={url[:60]}... sink={audio_sink}\n")
            except Exception:
                pass
        except Exception as e:
            self._playing = False
            self._title_label.setText("Streamfehler")
            try:
                with open(os.path.join(CONFIG_DIR, "stream_error.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: {type(e).__name__}: {e}\n")
            except Exception:
                pass
        return

    @pyqtSlot()
    def _startMainTimersSlot(self):
        """Startet Uhr- und Backend-Timer nur im Objekt-Thread (vermeidet QBasicTimer-Warnung)."""
        if QThread.currentThread() != self.thread():
            QTimer.singleShot(100, self._startMainTimersSlot)
            return
        self._clock_timer.start(CLOCK_INTERVAL_MS)
        self._backend_check_timer.start(5000)

    @pyqtSlot()
    def startBackendCheckTimerSlot(self):
        """Qt-Slot: startet Backend-Check-Timer (nur im Hauptthread)."""
        self._backend_check_timer.start(5000)

    @pyqtSlot()
    def startClockTimerSlot(self):
        """Qt-Slot: startet Uhrtimer (nur im Hauptthread per QueuedConnection)."""
        self._clock_timer.start(CLOCK_INTERVAL_MS)

    @pyqtSlot()
    def startStreamTimersSlot(self):
        """Qt-Slot: startet alle Stream-Timer nur im Objekt-Thread (QBasicTimer-Warnung vermeiden)."""
        if QThread.currentThread() != self.thread():
            QTimer.singleShot(100, self.startStreamTimersSlot)
            return
        self._metadata_timer.start(METADATA_INTERVAL_MS)
        self._metadata_check_timer.start(250)
        self._vu_timer.start(20)
        self._gst_bus_timer.start(200)

    def _stop_stream(self):
        self._metadata_timer.stop()
        self._metadata_check_timer.stop()
        self._vu_timer.stop()
        self._gst_bus_timer.stop()
        for ch in (0, 1, 2):
            self._set_led_strip(ch, 0)
        if self._old_default_sink:
            pactl = _pactl_path()
            if pactl:
                try:
                    subprocess.run(
                        [pactl, "set-default-sink", self._old_default_sink],
                        capture_output=True, text=True, timeout=2, env=_pactl_env()
                    )
                    self._old_default_sink = None
                except Exception:
                    pass
        if self._gst_player and self._gst_player.is_active:
            self._gst_player.stop()
        self._playing = False

    @pyqtSlot()
    def _apply_pending_metadata_slot(self):
        """Slot: wendet im Hauptthread die vom Worker gesetzten _pending_metadata an (nur wenn Sender noch derselbe)."""
        meta = getattr(self, "_pending_metadata", None)
        force_show = getattr(self, "_pending_metadata_force_show", False)
        fetched_url = getattr(self, "_pending_metadata_url", "")
        if meta is None:
            return
        current_url = (self._current_station.get("stream_url") or self._current_station.get("url") or "").strip()
        if fetched_url and current_url and fetched_url != current_url:
            return  # Sender gewechselt, veraltete Metadaten ignorieren
        try:
            self._apply_metadata(meta, force_show=force_show)
        except Exception:
            pass

    def _check_and_apply_metadata(self):
        """Prüft ob neue Metadaten in last_metadata.json verfügbar sind und wendet sie an (UI-Thread)."""
        if not self._playing:
            return
        try:
            p = os.path.join(CONFIG_DIR, "last_metadata.json")
            if not os.path.isfile(p):
                return
            mtime = os.path.getmtime(p)
            now = datetime.now().timestamp()
            if now - mtime > 30.0:
                return  # Datei zu alt (30 s Toleranz)
            if not hasattr(self, "_last_metadata_mtime"):
                self._last_metadata_mtime = 0
            if mtime <= self._last_metadata_mtime:
                return
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_url = (data.get("stream_url") or "").strip()
            current_url = (self._current_station.get("stream_url") or self._current_station.get("url") or "").strip()
            if file_url and current_url and file_url != current_url:
                return  # Metadaten gehören zu anderem Sender
            meta = data.get("meta", {})
            if meta:
                self._last_metadata_mtime = mtime
                try:
                    self._apply_metadata(meta, force_show=True)
                except Exception as e:
                    # Fehler beim Anwenden der Metadaten loggen
                    try:
                        os.makedirs(CONFIG_DIR, exist_ok=True)
                        with open(os.path.join(CONFIG_DIR, "metadata_check_error.log"), "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now().isoformat()}: Fehler beim Aufruf von _apply_metadata: {type(e).__name__}: {str(e)}\n")
                            import traceback
                            f.write(traceback.format_exc())
                    except Exception:
                        pass
        except Exception as e:
            # Fehler loggen für Debugging (Datei/JSON)
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(os.path.join(CONFIG_DIR, "metadata_check_error.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: Fehler in _check_and_apply_metadata: {type(e).__name__}: {str(e)}\n")
                    import traceback
                    f.write(traceback.format_exc())
            except Exception:
                pass
        # Fallback: dieselbe Quelle wie der Lautstärkeregler (PulseAudio/PipeWire Stream-Metadaten)
        try:
            meta_sys = _get_system_stream_metadata()
            if meta_sys and (meta_sys.get("title") or meta_sys.get("artist")):
                # „Artist - Titel“ aus media.title zerlegen, falls nur title gesetzt
                title = (meta_sys.get("title") or "").strip()
                artist = (meta_sys.get("artist") or "").strip()
                if title and not artist and (" - " in title or " – " in title or "\u2013" in title):
                    for sep in (" - ", " – ", " \u2013 "):
                        if sep in title:
                            parts = title.split(sep, 1)
                            artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                            title = (parts[1].strip() or title) if len(parts) > 1 else title
                            break
                applied = {"title": title, "artist": artist, "show": (meta_sys.get("show") or "").strip()}
                self._apply_metadata(applied, force_show=True)
        except Exception:
            pass

    def _apply_metadata(self, meta: dict, force_show: bool = False):
        """Metadaten in UI anzeigen. Schreibt immer metadata_applied.json; UI-Update nur wenn _playing oder force_show.
        force_show=True: Meta wurde beim Abruf während Wiedergabe empfangen – UI trotzdem aktualisieren (vermeidet Race)."""
        # UI-Updates nur im Hauptthread (Qt erlaubt keine Änderungen an Widgets aus anderen Threads)
        if QThread.currentThread() != self.thread():
            QTimer.singleShot(0, lambda m=meta, f=force_show: self._apply_metadata(m, f))
            return
        playing_now = getattr(self, "_playing", False)
        # Zuerst: Immer metadata_applied.json schreiben (auch wenn UI-Update später fehlschlägt)
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            p = os.path.join(CONFIG_DIR, "metadata_applied.json")
            debug_data = {
                "show": (meta.get("show") or meta.get("server_name") or "").strip(),
                "title": (meta.get("title") or "").strip(),
                "artist": (meta.get("artist") or "").strip(),
                "song": (meta.get("song") or "").strip(),
                "bitrate": meta.get("bitrate"),
                "timestamp": datetime.now().isoformat(),
                "raw_meta": meta,
                "playing": playing_now,
                "force_show": force_show,
                "station": (self._current_station or {}).get("name", "Unknown"),
            }
            with open(p, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
            # Debug-Log nur bei PI_INSTALLER_DSI_DEBUG=1 (reduziert Speicher/Disk-Last)
            if os.environ.get("PI_INSTALLER_DSI_DEBUG"):
                try:
                    with open(os.path.join(CONFIG_DIR, "metadata_apply_debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()}: metadata_applied.json (playing={playing_now}, force_show={force_show})\n")
                except Exception:
                    pass
        except Exception as e:
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(os.path.join(CONFIG_DIR, "metadata_applied_error.log"), "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: Fehler beim Schreiben metadata_applied.json: {type(e).__name__}: {str(e)}\n")
                    import traceback
                    f.write(traceback.format_exc())
            except Exception:
                pass

        if not playing_now and not force_show:
            return
        if not hasattr(self, "_title_label") or not self._title_label:
            QTimer.singleShot(100, lambda m=meta, f=force_show: self._apply_metadata(m, f))
            return

        self._metadata = meta
        station_name = (self._current_station or {}).get("name", "Livestream")
        current_url = (self._current_station or {}).get("stream_url") or (self._current_station or {}).get("url") or ""
        is_saw = "stream.radiosaw.de" in (current_url or "")
        is_rsa = "rsa-sachsen.de" in (current_url or "")
        is_mdr_aktuell = "mdr.de" in (current_url or "") or "MDR Aktuell" in (station_name or "")
        is_rbb888 = "rbb888" in (current_url or "") or "rbb 88.8" in (station_name or "") or "88.8" in (station_name or "")
        show = (meta.get("show") or meta.get("server_name") or "").strip()
        title = (meta.get("title") or "").strip()
        artist = (meta.get("artist") or "").strip()
        song = (meta.get("song") or "").strip()
        bitrate = meta.get("bitrate")
        # Radio SAW / R.SA: oft keine echten Titel/Interpret-Metadaten → Hinweis anzeigen
        if is_saw and not (artist or song) and (not title or title.upper() in ("LIVE", "RADIO SAW", "RADIO SAW SIMULCAST") or "simulcast" in title.lower() or "saw " in title.lower()[:20]):
            meta = dict(meta)
            meta["metadata_unsupported"] = True
        if is_rsa and not (artist or song) and (not title or title.upper() in ("LIVE", "R.SA", "RSA")):
            meta = dict(meta)
            meta["metadata_unsupported"] = True
        if is_mdr_aktuell and not (artist or song) and (not title or title.upper() in ("LIVE", "MDR AKTUELL", "MDR")):
            meta = dict(meta)
            meta["metadata_unsupported"] = True
        if is_rbb888 and not (artist or song) and (not title or title.upper() in ("LIVE", "RBB 88.8", "RBB")):
            meta = dict(meta)
            meta["metadata_unsupported"] = True
        # Erkennung: Show-Metadaten die fälschlicherweise als Titel/Interpret kommen (z. B. "Die Show", "1LIVE Liebesalarm")
        # Wenn title ein Show-Name ist oder artist den Sendernamen enthält → als show behandeln
        show_keywords = ("show", "magazin", "alarm", "programm", "sendung", "talk", "morgen", "mittag", "abend")
        title_lower = title.lower()
        artist_lower = artist.lower()
        station_name_lower = station_name.lower()
        # Prüfe ob title ein Show-Name ist (enthält Show-Keywords oder ist sehr kurz wie "Die Show")
        is_show_title = False
        if title and (any(kw in title_lower for kw in show_keywords) or (len(title) < 20 and title_lower in ("die show", "show", "live show"))):
            is_show_title = True
        # Prüfe ob artist den Sendernamen enthält (z. B. "1LIVE Liebesalarm" → artist="1LIVE Liebesalarm")
        is_show_artist = False
        if artist and station_name_lower and station_name_lower in artist_lower:
            is_show_artist = True
        # Wenn title oder artist als Show erkannt wurden → als show behandeln, nicht als Titel/Interpret
        if is_show_title or is_show_artist:
            if is_show_title and not show:
                show = title
                title = ""
            if is_show_artist and not show:
                if show:
                    show = f"{show} · {artist}"
                else:
                    show = artist
                artist = ""
        # Backend liefert oft "Artist: Song" oder "Artist - Song" nur in title – aufteilen
        if title and not (artist or song):
            for sep in (" - ", " – ", " \u2013 ", " : ", ":"):
                if sep in title:
                    parts = title.split(sep, 1)
                    artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                    song = (parts[1].strip() or title) if len(parts) > 1 else title
                    break

        # Redundanzen entfernen: Sendername aus Anzeige-Strings streichen, wenn er vorne dran steht
        def strip_station_prefix(text: str) -> str:
            if not text or not station_name:
                return text
            t, s = text.strip(), station_name.strip()
            if not s:
                return t
            if t.upper() == s.upper():
                return ""
            if t.upper().startswith((s + " - ").upper()) or t.upper().startswith((s + "-").upper()):
                return t[len(s):].lstrip(" -").strip()
            return t

        # Titel-Zeile: nur Liedtitel (Song), nie „Artist - Titel“ oder Sendername – Sendername bleibt oben
        title_to_show = ""
        if song and song.strip():
            title_to_show = strip_station_prefix(song)
            if title_to_show:
                title_to_show = title_to_show[:60] + ("…" if len(title_to_show) > 60 else "")
        if not title_to_show and title and title.strip():
            title_upper = title.strip().upper()
            if title_upper != "LIVE":
                title_to_show = strip_station_prefix(title)
                if title_to_show:
                    title_to_show = title_to_show[:60] + ("…" if len(title_to_show) > 60 else "")

        if title_to_show:
            self._title_label.setText(title_to_show)
        else:
            current_text = self._title_label.text()
            if current_text == "Streamfehler" or not current_text or current_text == "":
                self._title_label.setText("")  # Sendername steht oben, hier nichts überschreiben

        # Interpret-Zeile: nur Interpret (Artist), getrennt vom Titel – keine Dopplung
        artist_to_show = ""
        if artist and artist.strip():
            artist_to_show = strip_station_prefix(artist)
            if artist_to_show and artist_to_show != title_to_show:
                artist_to_show = artist_to_show[:60] + ("…" if len(artist_to_show) > 60 else "")
            elif artist_to_show == title_to_show:
                artist_to_show = ""
        if artist_to_show:
            self._artist_label.setText(artist_to_show)
        elif meta.get("metadata_unsupported"):
            self._artist_label.setText("Titel/Interpret für diesen Sender derzeit nicht verfügbar.")
        else:
            self._artist_label.setText("")

        # „Es läuft:“ nur echten Sendungsnamen (Programm/Moderator), nie Titel oder Interpret
        es_laeuft = strip_station_prefix(show)
        if es_laeuft and es_laeuft.upper() == station_name.upper():
            es_laeuft = ""
        if es_laeuft and (es_laeuft == title_to_show or es_laeuft == artist_to_show):
            es_laeuft = ""
        # Kein Titel/Interpret hinter „Es läuft:“ – die stehen darunter
        if es_laeuft and (title_to_show or artist_to_show):
            combined = f"{artist_to_show} - {title_to_show}".strip(" -") if (artist_to_show and title_to_show) else (artist_to_show or title_to_show)
            if es_laeuft == combined or es_laeuft == title_to_show or es_laeuft == artist_to_show:
                es_laeuft = ""
        if not es_laeuft and meta.get("metadata_unsupported"):
            region = (self._current_station or {}).get("region", "").strip()
            if region:
                es_laeuft = region  # z. B. Sachsen-Anhalt bei Radio SAW
        if es_laeuft:
            # Nur echter Sendungsname; Titel/Interpret stehen darunter
            text = "Es läuft: " + (es_laeuft[:100] + ("…" if len(es_laeuft) > 100 else ""))
            self._show_label.setText(text)
        else:
            # „Es läuft:“ immer anzeigen, auch wenn kein Sendungsname vorliegt
            self._show_label.setText("Es läuft:")
        
        # Audioqualität (Zusatzdaten) unter dem Logo
        if bitrate:
            self._quality_label.setText(f"{bitrate} kbps")
            self._set_led_strip(2, min(100, int(bitrate) if bitrate else 0))
        else:
            self._quality_label.setText("")
            if self._playing:
                self._set_led_strip(2, 80)
        # Schriftgrößen an verfügbaren Platz anpassen (z. B. bei langen Titeln)
        QTimer.singleShot(0, self._update_radio_display_fonts)

    def _on_vu_slider(self, value: int):
        """Schiebeschalter: 0 = LED (Digital), 1 = Analog."""
        self._vu_mode = "analog" if value == 1 else "led"
        self._vu_led_container.setVisible(self._vu_mode == "led")
        self._vu_analog_container.setVisible(self._vu_mode == "analog")
        if self._vu_mode == "analog":
            vol = getattr(self, "_volume_slider", None)
            cap = vol.value() if vol else 100
            self._vu_analog_widgets[0].set_value(min(getattr(self, "_vu_val_0", 0), cap))
            self._vu_analog_widgets[1].set_value(min(getattr(self, "_vu_val_1", 0), cap))
            self._vu_analog_widgets[2].set_value(min(self._metadata.get("bitrate") or 80 if self._playing else 0, cap))

    def _toggle_vu_mode(self):
        """LED / Analog umschalten (z. B. für Tastatur)."""
        try:
            s = self._vu_mode_slider
            s.setValue(0 if s.value() == 1 else 1)
        except Exception:
            pass

    def _set_led_strip(self, channel: int, value: int):
        """10 LEDs: Index 0=unten (grün), 6–7 gelb, 8–9 rot. L/R durch Lautstärke begrenzt, Signal unbegrenzt."""
        raw = max(0, min(100, value))
        # Nur L/R (Kanal 0, 1) durch Lautstärke begrenzen; Signal (Kanal 2) immer voll anzeigen
        if channel < 2:
            vol = getattr(self, "_volume_slider", None)
            max_val = vol.value() if vol else 100
            value = min(raw, max_val)
        else:
            value = raw
        if channel >= 0 and channel < len(self._vu_leds):
            lit = min(10, int((value / 100) * 10.99))
            off = "#252525"  # Restleuchten wenn keine Anzeige
            green, yellow, red_c = "#22c55e", "#eab308", "#dc2626"
            # Signal-Säule (Kanal 2): nur grüne LEDs; L/R (0, 1): grün → gelb → rot
            signal_green_only = channel == 2
            for i, f in enumerate(self._vu_leds[channel]):
                on = i < lit
                if signal_green_only:
                    c = green if on else off
                elif i < 6:
                    c = green if on else off
                elif i < 8:
                    c = yellow if on else off
                else:
                    c = red_c if on else off
                f.setStyleSheet(f"background-color: {c}; border: none; border-radius: 1px;")
        if channel >= 0 and channel < len(self._vu_analog_widgets):
            self._vu_analog_widgets[channel].set_value(value)

    def _update_vu(self):
        """VU L/R aus GStreamer-Level-Pegeln; Senderstärke (Kanal 2) aus Bitrate."""
        if not self._playing:
            return
        peaks = None
        if self._gst_player and getattr(self._gst_player, "get_peak_levels", None):
            try:
                peaks = self._gst_player.get_peak_levels()
            except Exception:
                pass
        if peaks is not None and len(peaks) >= 2 and (peaks[0] > 0 or peaks[1] > 0):
            self._vu_val_0 = max(0, min(100, int(peaks[0])))
            self._vu_val_1 = max(0, min(100, int(peaks[1])))
        else:
            for ch in (0, 1):
                w = getattr(self, f"_vu_val_{ch}", 50)
                w = min(100, max(0, w + random.randint(-8, 12)))
                setattr(self, f"_vu_val_{ch}", w)
        for ch in (0, 1):
            self._set_led_strip(ch, getattr(self, f"_vu_val_{ch}", 0))
        level = (getattr(self, "_vu_val_0", 0) + getattr(self, "_vu_val_1", 0)) / 2.0
        if getattr(self, "_waveform_widget", None) is not None:
            self._waveform_widget.append(level)
        if getattr(self, "_spectrum_widget", None) is not None:
            n_bands = 24
            fft_buf = getattr(self, "_fft_buffer", None)
            if _NUMPY_AVAILABLE and fft_buf is not None and len(fft_buf) >= 128:
                arr = np.array(list(fft_buf)[-128:], dtype=np.float64)
                arr = arr - np.mean(arr)
                window = np.hanning(128)
                arr = arr * window
                fft = np.fft.rfft(arr)
                mag = np.abs(fft)
                bands = _fft_to_log_bands(mag, n_bands)
                prev = getattr(self, "_spectrum_bands", [0.0] * n_bands)
                decay = 0.85
                bands = [prev[i] * decay + bands[i] * (1 - decay) for i in range(n_bands)]
                self._spectrum_bands = bands
                self._spectrum_widget.set_bands(bands)
            else:
                prev = getattr(self, "_spectrum_bands", [0.0] * n_bands)
                if len(prev) != n_bands:
                    prev = (prev + [0.0] * n_bands)[:n_bands]
                decay = 0.88
                bands = [0.0] * n_bands
                for i in range(n_bands):
                    bands[i] = prev[i] * decay + level * (0.25 + 0.75 * (1 + sin(i * 0.8)) / 2) * (1 - decay)
                self._spectrum_bands = bands
                self._spectrum_widget.set_bands(bands)
            if fft_buf is not None:
                fft_buf.append(level)

    def _poll_metadata(self):
        url = (self._current_station.get("stream_url") or self._current_station.get("url") or "").strip()
        if not url or not self._playing:
            return
        def do():
            try:
                # Metadaten abrufen: zuerst Backend, bei leerem Ergebnis ICY direkt aus dem Stream (wie Lautstärkeregler)
                meta_raw = _fetch_metadata(url)
                if not isinstance(meta_raw, dict):
                    meta_raw = {}
                meta = {k: v for k, v in meta_raw.items() if k != "status"}
                # Wenn Backend keine Metadaten liefert: immer ICY direkt aus dem Stream versuchen (mehr Sender zeigen dann Titel)
                if not (meta.get("title") or meta.get("artist") or meta.get("song")):
                    icy = _fetch_icy_metadata_direct(url)
                    if icy and (icy.get("title") or icy.get("artist") or icy.get("song")):
                        meta = dict(icy)
                title_val = (meta.get("title") or "").strip()
                # Radio SAW / R.SA: Sender-/Stream-Namen gelten oft nicht als echte Titel
                is_saw_url = "stream.radiosaw.de" in url
                is_rsa_url = "rsa-sachsen.de" in url
                saw_station_name_only = is_saw_url and (
                    not title_val or title_val.upper() in ("LIVE", "RADIO SAW", "RADIO SAW SIMULCAST")
                    or "simulcast" in title_val.lower() or title_val.lower().startswith(("radio saw", "saw "))
                )
                rsa_station_only = is_rsa_url and (not title_val or title_val.upper() in ("LIVE", "R.SA", "RSA"))
                has_real_meta = (title_val not in ("", "Live") and not saw_station_name_only and not rsa_station_only) or (meta.get("artist") or meta.get("song"))
                if not has_real_meta:
                    if is_saw_url and not (meta.get("artist") or meta.get("song")) and (not (meta.get("title") or "").strip() or saw_station_name_only):
                        meta = dict(meta)
                        meta["metadata_unsupported"] = True
                        meta["title"] = ""
                        meta["song"] = ""
                    if is_rsa_url and not (meta.get("artist") or meta.get("song")) and (not title_val or rsa_station_only):
                        meta = dict(meta) if isinstance(meta, dict) else {}
                        meta["metadata_unsupported"] = True
                        meta["title"] = meta.get("title") or ""
                        meta["song"] = meta.get("song") or ""
                try:
                    os.makedirs(CONFIG_DIR, exist_ok=True)
                    if os.environ.get("PI_INSTALLER_DSI_DEBUG"):
                        p = os.path.join(CONFIG_DIR, "metadata_poll.log")
                        with open(p, "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now().isoformat()}: BACKEND={BACKEND_BASE} Station={self._current_station.get('name', 'Unknown')} playing={self._playing}\n")
                            f.write(f"  title={meta.get('title')!r} artist={meta.get('artist')!r} song={meta.get('song')!r}\n")
                    p2 = os.path.join(CONFIG_DIR, "last_metadata.json")
                    with open(p2, "w", encoding="utf-8") as f:
                        json.dump({"meta": meta, "stream_url": url, "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

                # Metadaten im Hauptthread anwenden (Qt-Signal → Slot garantiert im Hauptthread, auch auf dem Pi)
                meta_copy = dict(meta)
                playing_state = self._playing
                self._pending_metadata = meta_copy
                self._pending_metadata_force_show = playing_state
                self._pending_metadata_url = url
                self._metadataApplyRequested.emit()
            except Exception as e:
                try:
                    os.makedirs(CONFIG_DIR, exist_ok=True)
                    p = os.path.join(CONFIG_DIR, "metadata_error.log")
                    with open(p, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()}: Metadaten-Abruf fehlgeschlagen: {type(e).__name__}: {str(e)}\n")
                        import traceback
                        f.write(traceback.format_exc())
                except Exception:
                    pass
                playing_state = self._playing
                self._pending_metadata = {}
                self._pending_metadata_force_show = playing_state
                self._pending_metadata_url = ""
                self._metadataApplyRequested.emit()
        threading.Thread(target=do, daemon=True).start()


    def _position_close_button(self):
        """Sensor-Button ist in der oberen Leiste im Layout – keine Positionierung nötig."""
        pass
    
    def _move_to_dsi_display(self):
        """Unter X11: Fenster auf DSI-1 Display verschieben (Position 0x1440)."""
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "x11" or os.environ.get("DISPLAY", "").startswith(":"):
            try:
                # Prüfe ob xdotool verfügbar ist
                import subprocess
                if subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
                    # Warte kurz, damit Fenster vollständig erstellt ist
                    QTimer.singleShot(200, lambda: self._move_window_x11())
                else:
                    # Fallback: Direkt mit PyQt6-Geometrie versuchen
                    self._move_window_pyqt()
            except Exception:
                # Fallback: Direkt mit PyQt6-Geometrie versuchen
                self._move_window_pyqt()
    
    def _move_window_x11(self):
        """Verschiebt Fenster mit xdotool auf DSI-1 Display (Position 0x1440)."""
        try:
            import subprocess
            # Fenster-ID finden (Fenstertitel)
            result = subprocess.run(
                ["xdotool", "search", "--name", WINDOW_TITLE],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                win_id = result.stdout.strip().split("\n")[0]
                # Fenster auf Position 0x1440 verschieben (DSI-1 Display)
                subprocess.run(
                    ["xdotool", "windowmove", win_id, "0", "1440"],
                    timeout=2
                )
        except Exception:
            pass
    
    def _move_window_pyqt(self):
        """Verschiebt Fenster mit PyQt6-Geometrie auf DSI-1 Display."""
        try:
            # DSI-1 Display-Geometrie: 0x1440, Größe 480x800 (Portrait)
            # Unter X11 ist das die Position im virtuellen Desktop
            screen = QApplication.primaryScreen()
            if screen:
                # Prüfe ob wir mehrere Screens haben
                screens = QApplication.screens()
                if len(screens) > 1:
                    # DSI-1 sollte bei Position (0, 1440) sein
                    # Verschiebe Fenster dorthin
                    self.move(0, 1440)
                else:
                    # Nur ein Screen - versuche trotzdem Position zu setzen
                    self.move(0, 1440)
        except Exception:
            pass
    
    def _check_audio_output(self):
        """Prüft ob das richtige Audio-Ausgabegerät verwendet wird (PulseAudio/PipeWire)."""
        try:
            pactl = _pactl_path()
            if not pactl:
                # Kein PulseAudio - ALSA wird verwendet
                # Prüfe verfügbare ALSA-Geräte
                try:
                    result = subprocess.run(
                        ["aplay", "-l"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        # Zeige verfügbare ALSA-Geräte in Debug-Log
                        try:
                            debug_file = os.path.join(CONFIG_DIR, "alsa_devices.log")
                            with open(debug_file, "w", encoding="utf-8") as f:
                                f.write(f"{datetime.now().isoformat()}: ALSA-Geräte:\n{result.stdout}\n")
                        except Exception:
                            pass
                except Exception:
                    pass
                return
            
            env = _pactl_env()
            result = subprocess.run(
                [pactl, "info"],
                capture_output=True,
                text=True,
                timeout=2,
                env=env,
            )
            if result.returncode == 0:
                sink_result = subprocess.run(
                    [pactl, "get-default-sink"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    env=env,
                )
                if sink_result.returncode == 0:
                    sink_name = sink_result.stdout.strip()
                    # FREENOVE: Bei Freenove Computer Case ist HDMI-Audio OK (Mediaboard extrahiert Audio aus HDMI)
                    # Prüfe ob Freenove-Gehäuse erkannt wird (I2C Expansion-Board)
                    is_freenove = False
                    try:
                        for bus in (1, 0, 6, 7):
                            result_i2c = subprocess.run(
                                [f"i2cget", "-y", str(bus), "0x21", "0xfd"],
                                capture_output=True,
                                timeout=1
                            )
                            if result_i2c.returncode == 0:
                                is_freenove = True
                                break
                    except Exception:
                        pass
                    
                    # Warnung nur anzeigen, wenn kein Freenove-Gehäuse erkannt wurde
                    if "hdmi" in sink_name.lower() and not is_freenove:
                        # Warnung anzeigen (nur einmal)
                        if not hasattr(self, "_audio_warning_shown"):
                            self._audio_warning_shown = True
                            # Finde verfügbare nicht-HDMI-Sinks
                            available_sinks = _find_audio_sink()
                            msg = f"Aktuelles Standard-Ausgabegerät: {sink_name}\n\n"
                            if available_sinks:
                                msg += f"Verfügbares Gerät (wird automatisch verwendet): {available_sinks}\n\n"
                            msg += "Für Ton auf dem Gehäuse-Lautsprecher:\n"
                            msg += "Einstellungen → Sound → Ausgabegerät auf\n"
                            msg += "'Gehäuse-Lautsprecher' oder 'Headphones' setzen.\n\n"
                            msg += "Die App versucht automatisch, das richtige Gerät zu verwenden."
                            QMessageBox.information(
                                self,
                                "Audio-Ausgabegerät",
                                msg
                            )
        except Exception:
            # PulseAudio nicht verfügbar oder Fehler - ignorieren
            pass
    
    def _update_radio_display_fonts(self):
        """Passt die Schriftgrößen der Senderanzeige an die verfügbare Breite an (kleiner bei wenig Platz)."""
        if not getattr(self, "_radio_display_frame", None) or not self._radio_display_frame.isVisible():
            return
        w = self._radio_display_frame.width()
        logo = getattr(self, "_radio_display_logo_width", 90)
        margins = 16
        available = max(80, w - logo - margins)
        sizes = getattr(self, "_radio_display_font_sizes", {})
        min_pt = 9
        labels = [
            (self._station_label, sizes.get("station", 22), True),
            (self._genre_label, sizes.get("genre", 14), False),
            (self._show_label, sizes.get("show", 12), False),
            (self._title_label, sizes.get("title", 14), True),
            (self._artist_label, sizes.get("artist", 14), False),
        ]
        for label, base_pt, bold in labels:
            if label is None:
                continue
            text = (label.text() or "W").strip() or "W"
            pt = base_pt
            while pt >= min_pt:
                font = QFont("Sans", pt, QFont.Weight.Bold if bold else QFont.Weight.Normal)
                fm = QFontMetrics(font)
                if fm.horizontalAdvance(text) <= available:
                    break
                pt -= 1
            font = QFont("Sans", pt, QFont.Weight.Bold if bold else QFont.Weight.Normal)
            label.setFont(font)

    def _update_display_size_label(self):
        """Test: aktuelle Breite und Höhe des Radiodisplays im Display anzeigen."""
        if getattr(self, "_display_size_label", None) and getattr(self, "_radio_display_frame", None):
            w = self._radio_display_frame.width()
            h = self._radio_display_frame.height()
            self._display_size_label.setText(f"Breite: {w} px   Höhe: {h} px")

    def resizeEvent(self, event):
        """Bei Größenänderung X-Button neu positionieren, Schriftgrößen und Sender-Button-Umbruch anpassen."""
        super().resizeEvent(event)
        self._position_close_button()
        self._update_display_size_label()
        QTimer.singleShot(0, self._update_radio_display_fonts)
        # Sender-Buttons umbrechen, wenn sich die Spaltenzahl durch neue Breite ändert
        w = self._btn_container.width()
        cell = STATION_BTN_WIDTH + STATION_BTN_SPACING
        new_cols = max(1, min(16, w // cell)) if w > 0 else 4
        if new_cols != getattr(self, "_last_btn_cols", 0):
            self._rebuild_station_buttons()
    
    def showEvent(self, event):
        """Fenstertitel früh setzen, damit Wayfire-Regel (DSI-1/TFT) greift."""
        self.setWindowTitle(WINDOW_TITLE)
        super().showEvent(event)
        QTimer.singleShot(0, self._position_close_button)
        QTimer.singleShot(100, self._update_radio_display_fonts)
        QTimer.singleShot(50, self._update_display_size_label)
        # Nach Layout: Sender-Buttons ggf. mit echter Containerbreite umbrechen (falls vorher width=0)
        QTimer.singleShot(150, self._reflow_station_buttons_if_needed)
        self._setup_screenshot_shortcut()
        QTimer.singleShot(0, self._move_to_dsi_display)
        # Uhr- und Backend-Timer bald nach show starten (Start optimiert)
        QTimer.singleShot(200, self._startMainTimersSlot)
        # Beim ersten Start: Sender auf Platz 1 direkt starten (keine Verzögerung)
        if not getattr(self, "_auto_start_done", False):
            def check_and_start():
                if self._favorites and self._current_station and (self._current_station.get("stream_url") or self._current_station.get("url")):
                    self._auto_start_done = True
                    self._start_stream()
                elif not self._favorites:
                    # Noch nicht geladen, nochmal versuchen
                    QTimer.singleShot(100, check_and_start)
            QTimer.singleShot(0, check_and_start)

    def _setup_screenshot_shortcut(self):
        """F10 und Strg+Shift+S für Screenshot (QShortcut, Kontext: ganze Anwendung)."""
        for seq in (QKeySequence(Qt.Key.Key_F10), QKeySequence("Ctrl+Shift+S")):
            shortcut = QShortcut(seq, self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(self._take_screenshot)
    
    def keyPressEvent(self, event):
        """Tastendruck-Ereignisse behandeln."""
        if event.key() == Qt.Key.Key_F10:
            self._take_screenshot()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def _take_screenshot(self):
        """Erstellt einen Screenshot der Radio-App, speichert in Datei und kopiert in den Zwischenspeicher."""
        try:
            # Fenster zeichnen und Event-Queue leeren, damit grab() den aktuellen Inhalt erfasst
            self.repaint()
            for _ in range(3):
                QApplication.processEvents()
            # Methode 1: Fenster grab()
            pixmap = self.grab()
            # Methode 2: Zentrales Widget (oft zuverlässiger unter Wayland/DSI)
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                central = self.centralWidget()
                if central:
                    pixmap = central.grab()
            # Methode 3: Screen mit Window-ID (X11)
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                screen = QApplication.primaryScreen()
                if screen:
                    wid = self.winId()
                    if wid:
                        pixmap = screen.grabWindow(wid)
            
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                QMessageBox.warning(self, "Screenshot", "Fehler: Leeres Bild. Fenster sichtbar?")
                return
            
            # Immer zuerst in Datei speichern (garantierter Erfolg)
            saved_path = None
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_path = os.path.join(CONFIG_DIR, f"dsi_radio_screenshot_{stamp}.png")
                if pixmap.save(saved_path, "PNG"):
                    saved_path = saved_path
                else:
                    saved_path = None
            except Exception:
                saved_path = None
            
            # Zusätzlich in Zwischenspeicher kopieren
            clipboard = QApplication.clipboard()
            success = False
            
            # Prüfe ob wir unter X11 oder Wayland sind
            is_x11 = os.environ.get("XDG_SESSION_TYPE", "").lower() == "x11" or os.environ.get("DISPLAY", "").startswith(":")
            is_wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" or os.environ.get("WAYLAND_DISPLAY", "")
            
            # Methode 1: Pixmap direkt setzen
            try:
                clipboard.setPixmap(pixmap)
                QApplication.processEvents()
                # Prüfen ob es funktioniert hat
                test_pixmap = clipboard.pixmap()
                if not test_pixmap.isNull() and test_pixmap.width() > 0:
                    success = True
            except Exception:
                pass
            
            # Methode 2: Als PNG-Bytes mit QMimeData kopieren (funktioniert besser unter Wayland)
            if not success:
                try:
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    # Pixmap als PNG speichern
                    if pixmap.save(temp_path, "PNG"):
                        # PNG-Datei lesen
                        with open(temp_path, "rb") as f:
                            png_data = QByteArray(f.read())
                        
                        # QMimeData erstellen und Daten setzen
                        mime_data = QMimeData()
                        mime_data.setData("image/png", png_data)
                        
                        # In Zwischenspeicher kopieren
                        clipboard.setMimeData(mime_data)
                        QApplication.processEvents()
                        
                        # Prüfen ob es funktioniert hat
                        test_pixmap = clipboard.pixmap()
                        if not test_pixmap.isNull() and test_pixmap.width() > 0:
                            success = True
                        
                        # Temporäre Datei löschen
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                except Exception:
                    # Fehler ignorieren und nächste Methode versuchen
                    pass
            
            # Methode 3: Fallback - temporäre Datei und xclip/wl-copy verwenden
            # Unter X11: xclip zuerst versuchen, unter Wayland: wl-copy
            if not success:
                try:
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    # Pixmap als PNG speichern
                    if pixmap.save(temp_path, "PNG"):
                        # Reihenfolge je nach Session-Typ anpassen
                        if is_x11:
                            # X11: xclip zuerst
                            commands = [
                                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", temp_path],
                                ["wl-copy", "--type", "image/png"]
                            ]
                        else:
                            # Wayland: wl-copy mit Mime-Type
                            commands = [
                                ["wl-copy", "--type", "image/png"],
                                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", temp_path]
                            ]
                        
                        for cmd in commands:
                            try:
                                import subprocess
                                if cmd[0] == "wl-copy":
                                    with open(temp_path, "rb") as f:
                                        result = subprocess.run(cmd, input=f.read(), timeout=2, capture_output=True)
                                else:
                                    # xclip benötigt Dateipfad (bereits in cmd enthalten)
                                    result = subprocess.run(cmd, timeout=2, capture_output=True)
                                
                                if result.returncode == 0:
                                    success = True
                                    break
                            except (FileNotFoundError, subprocess.TimeoutExpired):
                                continue
                        
                        # Temporäre Datei löschen
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # Meldung: Dateipfad (wenn gespeichert), Größe, Zwischenspeicher-Status
            size_info = f"{pixmap.width()}×{pixmap.height()} Pixel"
            if saved_path:
                msg = f"Screenshot gespeichert unter:\n{saved_path}\n{size_info}"
                if success:
                    msg += "\n\nUnd in den Zwischenspeicher kopiert."
                elif not success:
                    msg += "\n\nZwischenspeicher nicht verfügbar (wl-copy/xclip ggf. installieren)."
            else:
                msg = f"Screenshot in Zwischenspeicher kopiert.\n{size_info}" if success else f"Datei konnte nicht gespeichert werden. Zwischenspeicher: {'ja' if success else 'nein'}.\n{size_info}"
            QMessageBox.information(self, "Screenshot", msg)
        except Exception as e:
            import traceback
            error_msg = f"Fehler beim Erstellen des Screenshots:\n{str(e)}\n\n{traceback.format_exc()}"
            QMessageBox.warning(self, "Screenshot", error_msg)

    def closeEvent(self, event):
        self._stop_stream()
        event.accept()


def _desktop_file_installed() -> bool:
    """Prüft, ob die .desktop-Datei in einem Standard-Pfad liegt (für Portal/App-ID)."""
    for base in (
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
        "/usr/share",
    ):
        path = os.path.join(base, "applications", "pi-installer-dsi-radio.desktop")
        if os.path.isfile(path):
            return True
    return False


def main():
    # Qt-Logging für Portal-Fehler unterdrücken (harmlos, aber störend):
    # "Connection already associated with an application ID" bei zweiter Instanz / Wayland
    import os
    if "QT_LOGGING_RULES" not in os.environ:
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.services=false"
    
    app = QApplication(sys.argv)
    app.setApplicationName("PI-Installer DSI Radio")
    try:
        gst_player.init()
    except Exception:
        pass  # GStreamer optional; App zeigt sonst Installationshinweis
    # Tooltips mit weißer Schrift für DSI-Display (sonst auf dunklem Hintergrund nicht lesbar)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #1e293b; border: 1px solid #475569; padding: 4px; font-size: 11px; }")
    # Wayland app_id nur setzen, wenn .desktop-Datei installiert ist – sonst Fehler:
    # "Could not register app ID: App info not found for 'pi-installer-dsi-radio'"
    # Zusätzlich: Fehler abfangen falls bereits registriert (z.B. bei mehreren Instanzen)
    if hasattr(app, "setDesktopFileName") and _desktop_file_installed():
        try:
            app.setDesktopFileName("pi-installer-dsi-radio")
        except Exception:
            # Fehler ignorieren (z.B. "Connection already associated with an application ID")
            # Die App funktioniert auch ohne Portal-Registrierung
            pass
    try:
        w = DsiRadioWindow()
        w.setWindowTitle(f"{WINDOW_TITLE} v{RADIO_APP_VERSION}")
        w.show()
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(os.path.join(CONFIG_DIR, "startup_error.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}\n{err}\n\n")
        except Exception:
            pass
        QMessageBox.critical(
            None,
            "DSI Radio – Fehler",
            f"Beim Starten ist ein Fehler aufgetreten:\n\n{str(e)}\n\nDetails siehe: {CONFIG_DIR}/startup_error.log"
        )
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(os.path.join(CONFIG_DIR, "startup_error.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}\n{err}\n\n")
        except Exception:
            pass
        print(err, file=sys.stderr)
        sys.exit(1)
