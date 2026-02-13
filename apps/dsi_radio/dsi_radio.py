#!/usr/bin/env python3
"""
PI-Installer DSI Radio – Standalone PyQt6-App für Freenove 4,3" DSI.
Version 2.0: GStreamer-Wiedergabe (statt VLC/mpv). 20 Favoriten, Radio-Browser-API, Klavierlack-Design.
Wayfire: Fenstertitel „PI-Installer DSI Radio“ → start_on_output DSI-1 (TFT).
"""

# Radio-App-Version (2.0 = GStreamer-Umstellung)
RADIO_APP_VERSION = "2.0.0"

import os
import sys
import json
import random
import subprocess
import threading
import urllib.request
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
)
from PyQt6.QtCore import Qt, QTimer, QByteArray, QRectF, QBuffer, QIODevice, QMimeData, QMetaObject, Q_ARG, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush, QColor, QImage, QShortcut, QKeySequence
from math import pi, cos, sin

# GStreamer-Player (Version 2.0)
try:
    from . import gst_player
except ImportError:
    import gst_player

BACKEND_BASE = os.environ.get("PI_INSTALLER_BACKEND", "http://127.0.0.1:8000")
METADATA_INTERVAL_MS = 15000  # 15 Sekunden (reduziert Last auf Backend)
CLOCK_INTERVAL_MS = 1000
WINDOW_TITLE = "PI-Installer DSI Radio"
FAVORITES_MAX = 20
# Konfigurationsverzeichnis: absolut, damit es immer korrekt ist
_CONFIG_BASE = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_DIR = os.path.join(_CONFIG_BASE, "pi-installer-dsi-radio")
# Stelle sicher, dass Verzeichnis existiert
os.makedirs(CONFIG_DIR, exist_ok=True)
FAVORITES_FILE = os.path.join(CONFIG_DIR, "favorites.json")
LAST_STATION_FILE = os.path.join(CONFIG_DIR, "last_station.json")
THEME_FILE = os.path.join(CONFIG_DIR, "theme.txt")
FAVORITES_PER_PAGE = 9

try:
    from stations import RADIO_STATIONS, STATION_LOGO_FALLBACKS
except ImportError:
    RADIO_STATIONS = [
        {"id": "einslive", "name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "wdr2", "name": "WDR 2", "stream_url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "dlf", "name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "logo_url": "", "region": "Bundesweit", "genre": "Info"},
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


def load_favorites() -> List[Dict[str, Any]]:
    try:
        if os.path.isfile(FAVORITES_FILE):
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data[:FAVORITES_MAX]
    except Exception:
        pass
    return [{"id": s["id"], "name": s["name"], "stream_url": s["stream_url"], "logo_url": s.get("logo_url", ""), "region": s.get("region", ""), "genre": s.get("genre", "")} for s in RADIO_STATIONS[:FAVORITES_MAX]]


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
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0", "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=5) as resp:
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


def _fetch_logo(url: str) -> Optional[bytes]:
    if not url:
        return None
    # Zuerst Backend-Proxy versuchen (Wikimedia-User-Agent, CORS-frei)
    try:
        proxy_url = f"{BACKEND_BASE}/api/radio/logo?url={urllib.request.quote(url, safe='')}"
        req = urllib.request.Request(proxy_url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.read()
    except Exception:
        pass
    # Fallback: Direkt laden mit Wikimedia-konformem User-Agent
    try:
        ua = "PI-Installer/1.0 (Radio logo; +https://github.com)" if ("wikipedia.org" in url or "wikimedia.org" in url) else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.read()
    except Exception:
        return None


def _fetch_stations_search(name: str = "") -> List[Dict[str, Any]]:
    """Holt Sender vom Backend (radio-browser). Bei Fehler/Leer: [] – Aufrufer zeigt dann RADIO_STATIONS."""
    try:
        url = f"{BACKEND_BASE}/api/radio/stations/search?countrycode=DE&limit=200"
        if name.strip():
            url += "&name=" + urllib.request.quote(name.strip())
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            if isinstance(data, dict) and "stations" in data:
                return data["stations"] if isinstance(data["stations"], list) else []
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


class StationListDialog(QDialog):
    """Senderliste aus radio-browser.info: nur Sendername (keine URL), Checkbox = Favorit an/ab."""

    def __init__(self, parent: Optional[QMainWindow], current_favorites: List[Dict[str, Any]], theme_name: str = "Klavierlack"):
        super().__init__(parent)
        self.setWindowTitle("Senderliste – Favoriten (radio-browser.info)")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(THEMES.get(theme_name, STYLE_KLAVIERLACK))
        self._current_favorites = list(current_favorites)
        self._add_station = None
        self._favorite_urls = {f.get("stream_url") or f.get("url") or "" for f in self._current_favorites}
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
        self._list.itemChanged.connect(self._on_item_check_changed)
        layout.addWidget(self._list)
        layout.addWidget(QLabel("☑ = Favorit (max 20). Keine URL-Anzeige."))
        close_btn = QPushButton("Schließen")
        close_btn.setMinimumHeight(48)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self._do_search()

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
        self._favorite_urls = {f.get("stream_url") or f.get("url") or "" for f in self._current_favorites}
        if checked:
            if url in self._favorite_urls:
                return
            if len(self._current_favorites) >= FAVORITES_MAX:
                QMessageBox.information(self, "Favoriten", f"Maximal {FAVORITES_MAX} Sender.")
                item.setCheckState(Qt.CheckState.Unchecked)
                return
            fav = self._station_to_fav(s)
            self._current_favorites.append(fav)
            self._add_station = fav
        else:
            self._current_favorites = [f for f in self._current_favorites if (f.get("stream_url") or f.get("url") or "").strip() != url]
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
                ]

                def add_minimal():
                    for s in minimal:
                        item = QListWidgetItem(s["name"])
                        item.setData(Qt.ItemDataRole.UserRole, s)
                        item.setFlags(list_flags)
                        item.setCheckState(Qt.CheckState.Checked if (s.get("url") or "") in self._favorite_urls else Qt.CheckState.Unchecked)
                        self._list.addItem(item)

                try:
                    self._list.itemChanged.disconnect(self._on_item_check_changed)
                except Exception:
                    pass
                self._list.clear()
                self._favorite_urls = {f.get("stream_url") or f.get("url") or "" for f in self._current_favorites}

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
                            item.setCheckState(Qt.CheckState.Checked if (st.get("url") or "") in self._favorite_urls else Qt.CheckState.Unchecked)
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
                            item.setCheckState(Qt.CheckState.Checked if url in self._favorite_urls else Qt.CheckState.Unchecked)
                            self._list.addItem(item)
                except Exception:
                    pass
                if self._list.count() == 0:
                    add_minimal()

                try:
                    self._list.itemChanged.connect(self._on_item_check_changed)
                except Exception:
                    pass

            QTimer.singleShot(0, apply)
        threading.Thread(target=do, daemon=True).start()

    def get_added_station(self):
        return getattr(self, "_add_station", None)


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
        self.setWindowTitle(f"{WINDOW_TITLE} v{RADIO_APP_VERSION}")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
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
        QTimer.singleShot(500, self._check_backend_for_led)  # Erste Prüfung kurz nach Start
        # Player, Favorites und Theme nach UI-Build laden (nicht-blockierend)
        QTimer.singleShot(0, self._load_data_async)

    def _load_data_async(self):
        """Lädt Favorites und Theme asynchron nach UI-Build. Ab v2.0: GStreamer, kein externer Player."""
        self._favorites = load_favorites()
        self._theme = load_theme()
        # Beim Start: letzten gespielten Sender wiederherstellen, falls noch in Favoriten
        last = load_last_station()
        last_url = (last or {}).get("stream_url") or (last or {}).get("url") or ""
        if last_url and self._favorites:
            for f in self._favorites:
                if ((f.get("stream_url") or f.get("url") or "").strip() == last_url.strip()):
                    self._current_station = f
                    # UI sofort aktualisieren, damit Logo und Sendername vom zuletzt angehörten Sender erscheinen
                    if hasattr(self, "_station_label"):
                        self._station_label.setText(f.get("name", "—"))
                    if hasattr(self, "_show_label"):
                        self._show_label.setText("Es läuft:")
                    self._update_senderinfo()
                    self._update_logo()
                    break
        if self._favorites and not self._current_station:
            self._current_station = self._favorites[0]
            self._update_senderinfo()
            self._update_logo()
        # Sender-Buttons (Favoriten) neu aufbauen, nachdem Favoriten geladen wurden
        self._rebuild_station_buttons()
        # Nochmals nach kurzer Verzögerung, damit die 20 Favoriten-Buttons sicher angezeigt werden
        QTimer.singleShot(300, self._rebuild_station_buttons)
        # Hintergrund: Streams prüfen, Senderliste aktualisieren (einmal pro Start)
        threading.Thread(target=self._background_station_update, daemon=True).start()

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
            f"QLabel#backendLed {{ background-color: {color}; border-radius: 7px; border: 1px solid #0f172a; }}"
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
        central = QWidget()
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(4, 0, 4, 8)
        main_v.setSpacing(6)

        # Obere Leiste: Datum/Uhrzeit links, Rot/Grün-Sensor-Button (Aus/An) rechts
        top_bar = QFrame()
        top_bar.setStyleSheet("background: #1e293b; border: none; border-radius: 0; padding: 4px 6px;")
        top_bar.setFixedHeight(40)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(8, 4, 6, 4)
        top_bar_layout.setSpacing(8)
        clock_font = QFont("Sans", 14, QFont.Weight.Bold)
        self._clock_label = QLabel()
        self._clock_label.setFont(clock_font)
        self._clock_label.setStyleSheet("color: #94a3b8; border: none;")
        self._clock_label.setMinimumWidth(180)
        self._clock_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        top_bar_layout.addWidget(self._clock_label, 0, Qt.AlignmentFlag.AlignVCenter)
        top_bar_layout.addStretch(1)
        # Runde LED: Grün = Backend läuft, Rot = Backend nicht erreichbar (Senderliste/Metadaten)
        self._backend_led = QLabel()
        self._backend_led.setObjectName("backendLed")
        self._backend_led.setFixedSize(14, 14)
        self._backend_led.setToolTip("Backend-Status: Grün = erreichbar, Rot = nicht erreichbar")
        self._backend_led.setStyleSheet(
            "QLabel#backendLed { background-color: #dc2626; border-radius: 7px; border: 1px solid #0f172a; }"
        )
        top_bar_layout.addWidget(self._backend_led, 0, Qt.AlignmentFlag.AlignVCenter)
        # Rot/Grüner Sensor-Button: Grün = An, Klick = Radio beenden (kompakt für DSI-Bereich)
        self._close_btn = QPushButton("Aus")
        self._close_btn.setMinimumSize(32, 14)
        self._close_btn.setMaximumSize(40, 18)
        self._close_btn.setToolTip("Radio beenden")
        self._close_btn.clicked.connect(self.close)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #dc2626, stop:0.5 #dc2626, stop:0.5 #16a34a, stop:1 #16a34a);
                color: white; font-weight: bold; font-size: 11px;
                border: 1px solid #0f172a; border-radius: 3px;
                padding: 0 3px;
                min-height: 16px;
            }
            QPushButton:hover { border-color: #fbbf24; }
        """)
        top_bar_layout.addWidget(self._close_btn, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        main_v.addWidget(top_bar)

        # Radioanzeige: vollständige Breite, kein Abstand nach oben
        card = QFrame()
        card.setObjectName("display")
        card.setStyleSheet("background: transparent; border: none;")
        
        # Schwarzer Rahmen, schlank – mehr Platz für Anzeige
        black_frame = QFrame()
        black_frame.setStyleSheet("""
            background: #0c0c0c;
            border: 2px solid #000000;
            border-radius: 4px;
            padding: 0;
        """)
        black_frame_layout = QVBoxLayout(black_frame)
        black_frame_layout.setContentsMargins(3, 3, 3, 3)
        black_frame_layout.setSpacing(0)
        
        # Weißes Display mit Logo links, Text rechts (Portrait 480x800: mehr Höhe für DSI-1)
        green_display = QFrame()
        green_display.setStyleSheet("background: #ffffff; border: none; border-radius: 0px; padding: 4px;")
        green_display.setMinimumHeight(140)
        green_display.setMaximumHeight(360 if portrait else 220)
        green_display_layout = QVBoxLayout(green_display)
        green_display_layout.setContentsMargins(4, 4, 4, 4)
        green_display_layout.setSpacing(0)
        
        # Hauptbereich: Logo links, Text rechts (geringer Abstand zwischen Logo und Sendername/Titel)
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(2)
        
        # Logo-Bereich: nochmals 5 px verkleinert, damit links/rechts nicht abgeschnitten
        logo_container = QVBoxLayout()
        logo_container.setSpacing(2)
        self._logo_label = QLabel()
        # Logobereich: Portrait 85×85, Landscape 97×97
        logo_max = 85 if portrait else 97
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
        self._quality_label.setMaximumHeight(18)
        logo_container.addWidget(self._quality_label)
        logo_container.addStretch()
        content_row.addLayout(logo_container, 0)
        
        # Text-Bereich rechts: Sendername, Musikrichtung, Titel, Interpret, Sendung
        text_container = QVBoxLayout()
        text_container.setSpacing(3)
        text_container.setContentsMargins(0, 0, 0, 0)
        
        self._station_label = QLabel(self._current_station.get("name", "—"))
        self._station_label.setFont(QFont("Sans", 22, QFont.Weight.Bold))
        self._station_label.setStyleSheet("color: #0f172a; border: none;")
        self._station_label.setMinimumHeight(32)
        self._station_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        text_container.addWidget(self._station_label)
        
        # Musikrichtung / Bereich (z. B. Sachsen-Anhalt, 70er)
        self._genre_label = QLabel(self._current_station.get("genre", ""))
        self._genre_label.setFont(QFont("Sans", 14))
        self._genre_label.setStyleSheet("color: #0f172a; border: none;")
        text_container.addWidget(self._genre_label)
        
        # Laufende Sendung / Moderator („Es läuft:“ – darf zweizeilig sein)
        self._show_label = QLabel("")
        self._show_label.setFont(QFont("Sans", 12))
        self._show_label.setStyleSheet("color: #0f172a; border: none;")
        self._show_label.setWordWrap(True)
        self._show_label.setMinimumHeight(36)
        self._show_label.setMaximumHeight(80)
        self._show_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        text_container.addWidget(self._show_label)
        
        # Titel (Liedtitel oder „Interpret – Titel“)
        self._title_label = QLabel("")
        self._title_label.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self._title_label.setStyleSheet("color: #0f172a; border: none;")
        self._title_label.setWordWrap(True)
        self._title_label.setMinimumHeight(26)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_container.addWidget(self._title_label)
        
        # Interpret
        self._artist_label = QLabel("")
        self._artist_label.setFont(QFont("Sans", 14))  # Gleiche Größe wie Titel, aber nicht fett
        self._artist_label.setStyleSheet("color: #0f172a; border: none;")
        self._artist_label.setWordWrap(True)
        self._artist_label.setMinimumHeight(26)  # Gleiche Höhe wie Titel
        self._artist_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._artist_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_container.addWidget(self._artist_label)
        
        text_container.addStretch()
        content_row.addLayout(text_container, 1)
        
        green_display_layout.addLayout(content_row, 1)
        black_frame_layout.addWidget(green_display, 0)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card_layout.addWidget(black_frame)
        main_v.addWidget(card)
        
        # Restliche UI-Elemente in horizontalem Layout
        main_h = QHBoxLayout()
        main_h.setSpacing(8)
        left = QWidget()
        layout = QVBoxLayout(left)
        layout.setSpacing(12 if portrait else 8)
        layout.setContentsMargins(0, 0, 0, 0)

        # VU L/R + Signal: LED oder Analog; Schiebeschalter (Digital/Analog) am rechten Rand
        self._vu_mode = "led"
        self._vu_leds: List[List[QFrame]] = []
        self._vu_analog_widgets: List[AnalogGaugeWidget] = []
        vu_row = QHBoxLayout()
        vu_row.setSpacing(16 if portrait else 8)
        vu_row.setContentsMargins(0, 6 if portrait else 0, 0, 6 if portrait else 0)
        led_container = QWidget()
        led_layout = QHBoxLayout(led_container)
        led_layout.setContentsMargins(0, 0, 0, 0)
        led_layout.setSpacing(0)
        for ch, lab in enumerate(["L", "R", "Signal"]):
            if ch == 1:
                led_layout.addSpacing(24)
            elif ch == 2:
                led_layout.addSpacing(48)
            col = QVBoxLayout()
            lbl = QLabel(lab)
            lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            col.addWidget(lbl)
            strip = QWidget()
            strip.setFixedWidth(16)
            strip.setFixedHeight(100)
            strip_layout = QVBoxLayout(strip)
            strip_layout.setContentsMargins(0, 0, 0, 0)
            strip_layout.setSpacing(1)
            frames = []
            for _ in range(10):
                f = QFrame()
                f.setFixedHeight(8)
                f.setStyleSheet("background-color: #1e293b; border-radius: 1px;")
                frames.append(f)
            for idx in (9, 8, 7, 6, 5, 4, 3, 2, 1, 0):
                strip_layout.addWidget(frames[idx])
            self._vu_leds.append(frames)
            col.addWidget(strip)
            led_layout.addLayout(col)
        led_layout.addStretch(1)
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
            lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            col.addWidget(lbl)
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
        # D/A-Schiebeschalter: schöner gestylt
        vu_switch = QWidget()
        vu_switch_layout = QVBoxLayout(vu_switch)
        vu_switch_layout.setContentsMargins(0, 0, 0, 0)
        da_row = QHBoxLayout()
        da_row.setSpacing(4)
        d_lbl = QLabel("D")
        d_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold; background: transparent;")
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
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #475569, stop:1 #64748b);
                height: 18px;
                border-radius: 9px;
                border: 1px solid #334155;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #f1f5f9, stop:1 #cbd5e1);
                width: 20px;
                height: 20px;
                margin: -1px 0;
                border-radius: 10px;
                border: 1px solid #64748b;
            }
            QSlider::sub-page:horizontal { 
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0d9488, stop:1 #14b8a6); 
                border-radius: 9px; 
            }
            QSlider::add-page:horizontal { 
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #475569, stop:1 #64748b); 
                border-radius: 9px; 
            }
        """)
        da_row.addWidget(self._vu_mode_slider, 0, Qt.AlignmentFlag.AlignCenter)
        a_lbl = QLabel("A")
        a_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold; background: transparent;")
        a_lbl.setFixedWidth(16)
        a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        da_row.addWidget(a_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        vu_switch_layout.addLayout(da_row)
        vu_row.addWidget(vu_switch, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(vu_row)

        # Sender-Buttons + rechts: Lautstärke oberhalb, Umschalter (1/2 ▶) darunter
        self._btn_container = QWidget()
        self._btn_layout = QGridLayout(self._btn_container)
        self._btn_layout.setSpacing(8)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._station_buttons: List[QPushButton] = []
        self._page_btn: Optional[QPushButton] = None
        page_row = QHBoxLayout()
        page_row.addWidget(self._btn_container, 1)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        vol_column = QFrame()
        vol_column.setStyleSheet("background: #1e293b; border: 2px solid #c0c0c0; border-radius: 8px; padding: 6px;")
        vol_column.setFixedWidth(44)
        vol_column.setMinimumHeight(180)
        vol_layout = QVBoxLayout(vol_column)
        vol_layout.setContentsMargins(4, 6, 4, 6)
        vol_layout.setSpacing(4)
        vol_lbl = QLabel("Lautstärke")
        vol_lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
        vol_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_layout.addWidget(vol_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        self._volume_slider = QSlider(Qt.Orientation.Vertical)
        self._volume_slider.setMinimum(0)
        self._volume_slider.setMaximum(100)
        self._volume_slider.setValue(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        self._volume_slider.setStyleSheet("""
            QSlider::groove:vertical { background: #475569; width: 12px; border-radius: 6px; margin: 0 2px; }
            QSlider::handle:vertical { background: #0f172a; height: 24px; width: 24px; margin: 0 -6px; border-radius: 12px; }
            QSlider::sub-page:vertical { background: #64748b; border-radius: 6px; }
            QSlider::add-page:vertical { background: #475569; border-radius: 6px; }
        """)
        vol_layout.addWidget(self._volume_slider, 1, Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(vol_column, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._page_btn = QPushButton("1/2 ▶")
        self._page_btn.setFixedHeight(36)
        self._page_btn.setFixedWidth(56)
        self._page_btn.setToolTip("Seite wechseln")
        self._page_btn.clicked.connect(self._toggle_favorites_page)
        right_layout.addWidget(self._page_btn, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        page_row.addWidget(right_column, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(page_row)
        self._rebuild_station_buttons()

        # Senderliste (Abspielen/Pause entfernt – Sender startet beim Klick, Platz 1 beim ersten Start)
        row = QHBoxLayout()
        list_btn = QPushButton("📻 Senderliste")
        list_btn.setMinimumHeight(48)
        list_btn.setObjectName("play")
        list_btn.clicked.connect(self._open_station_list)
        row.addWidget(list_btn)
        layout.addLayout(row)

        hint = QLabel("Kein Ton? Einstellungen → Sound → Ausgabegerät: Gehäuse-Lautsprecher.")
        hint.setStyleSheet("color: #64748b; font-size: 9px;")
        hint.setMaximumHeight(20)
        layout.addWidget(hint)
        
        # Audio-Ausgabegerät beim Start prüfen (reduzierte Verzögerung)
        QTimer.singleShot(50, self._check_audio_output)

        main_h.addWidget(left, 1)
        main_v.addLayout(main_h)

        portrait = os.environ.get("PI_INSTALLER_DSI_PORTRAIT", "1").lower() in ("1", "true", "yes")
        if portrait:
            self.setMinimumSize(480, 800)
            self.setFixedSize(480, 800)  # DSI-1 voll ausnutzen
        else:
            self.setMinimumSize(380, 320)
            self.resize(800, 480)
        self._update_logo()
        self._update_senderinfo()
        self._update_clock()
        # Uhr- und Backend-Timer werden in showEvent per _startMainTimersSlot gestartet (500 ms Verzögerung)

    def _apply_theme(self, name: str):
        self._theme = name
        self.setStyleSheet(THEMES.get(name, STYLE_KLAVIERLACK))

    def _toggle_favorites_page(self):
        total = len(self._favorites)
        if total <= FAVORITES_PER_PAGE:
            return
        pages = (total + FAVORITES_PER_PAGE - 1) // FAVORITES_PER_PAGE
        self._favorites_page = (self._favorites_page + 1) % pages
        self._rebuild_station_buttons()

    def _rebuild_station_buttons(self):
        for b in self._station_buttons:
            b.deleteLater()
        self._station_buttons.clear()
        unavailable = getattr(self, "_unavailable_stream_urls", set())
        sorted_fav = sorted(self._favorites, key=lambda s: (s.get("name") or "").lower())
        start = self._favorites_page * FAVORITES_PER_PAGE
        page_fav = sorted_fav[start : start + FAVORITES_PER_PAGE]
        cols = 3
        for i, s in enumerate(page_fav):
            url = (s.get("stream_url") or s.get("url") or "").strip()
            no_stream = url in unavailable
            label = "kein Stream" if no_stream else _button_label(s.get("name", "?"))
            b = QPushButton(label)
            b.setProperty("station_id", s.get("id"))
            b.setCheckable(True)
            b.setChecked(s.get("id") == self._current_station.get("id"))
            b.setMinimumHeight(48)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            if no_stream:
                b.setStyleSheet("QPushButton { background-color: #dc2626; color: white; font-weight: bold; } QPushButton:checked { background-color: #b91c1c; }")
                b.setToolTip(f"{s.get('name', '?')}: Stream nicht erreichbar")
            b.clicked.connect(lambda checked=False, st=s: self._on_station(st))
            self._station_buttons.append(b)
            self._btn_layout.addWidget(b, i // cols, i % cols)
        if self._page_btn:
            total = len(self._favorites)
            self._page_btn.setVisible(total > FAVORITES_PER_PAGE)
            pages = (total + FAVORITES_PER_PAGE - 1) // FAVORITES_PER_PAGE
            cur = self._favorites_page + 1
            self._page_btn.setText("◀ %d/%d" % (cur, pages) if self._favorites_page > 0 else "%d/%d ▶" % (cur, pages))

    def _open_station_list(self):
        dlg = StationListDialog(self, self._favorites, self._theme)
        dlg.exec()
        self._reload_favorites()
        self._rebuild_station_buttons()

    def _update_clock(self):
        self._clock_label.setText(datetime.now().strftime("%d.%m.%Y  %H:%M"))

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
        was_playing = self._playing
        self._stop_stream()
        self._current_station = st
        save_last_station(st)
        for b in self._station_buttons:
            b.setChecked(b.property("station_id") == st.get("id"))
        self._station_label.setText(st.get("name", "—"))
        self._update_senderinfo()
        self._title_label.setText("")
        self._artist_label.setText("")
        self._show_label.setText("")
        self._quality_label.setText("")
        self._metadata = {}
        # Zuerst Stream starten (schneller Wechsel), Logo danach asynchron laden
        self._start_stream()
        QTimer.singleShot(0, self._update_logo)

    def _update_logo(self):
        """Logo anzeigen. Synchron laden (3s Timeout) für zuverlässige Anzeige und Screenshots."""
        station = self._current_station
        name = (station.get("name") or "?").strip()
        url = (station.get("logo_url") or "").strip()
        if not url:
            url = STATION_LOGO_FALLBACKS.get(name) or ""
        self._logo_label.setPixmap(QPixmap())
        self._logo_label.setText(name[:2] if name else "…")
        if not url:
            return
        data = _fetch_logo(url)
        if not data:
            return
        pix = QPixmap()
        pix.loadFromData(QByteArray(data))
        if pix.isNull():
            return
        # Logo mit 10 % Abstand im Bereich (nicht abschneiden)
        # Logo 85 % der Box (deutlich kleiner, wird nicht abgeschnitten)
        box = self._logo_label.width() or 85
        box_h = self._logo_label.height() or 85
        max_w = max(40, int(box * 0.85))
        max_h = max(40, int(box_h * 0.85))
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
                self._artist_label.setText("sudo apt install python3-gi gir1.2-gstreamer-1.0 gstreamer1.0-plugins-good gstreamer1.0-pulseaudio")
                err = gst_player.get_availability_error() or "Unbekannt"
                self._show_label.setText(f"Grund: {err}. Nach Installation: App neu starten.")
                return
            self._gst_player = gst_player.GstPlayer()

        self._stop_stream()

        url = (self._current_station.get("stream_url") or self._current_station.get("url") or "").strip()
        if not url:
            return

        audio_sink = _find_audio_sink()
        has_pulseaudio = _pactl_path() is not None

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
                except Exception:
                    pass

        try:
            def on_gst_error(err_str: str):
                QTimer.singleShot(0, lambda: self._title_label.setText("Streamfehler"))
                QTimer.singleShot(0, lambda: setattr(self, "_playing", False))

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
            self._gst_player.set_uri(url)
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
            QTimer.singleShot(500, self._poll_metadata)

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
        self._vu_timer.start(50)
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
        show = (meta.get("show") or meta.get("server_name") or "").strip()
        title = (meta.get("title") or "").strip()
        artist = (meta.get("artist") or "").strip()
        song = (meta.get("song") or "").strip()
        bitrate = meta.get("bitrate")
        # Radio SAW/streamABC: keine echten Metadaten → immer Hinweis + Region anzeigen
        if is_saw and not (artist or song) and (not title or title.upper() in ("LIVE", "RADIO SAW", "RADIO SAW SIMULCAST") or "simulcast" in title.lower() or "saw " in title.lower()[:20]):
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
            off, green, yellow, red_c = "#1e293b", "#22c55e", "#eab308", "#dc2626"
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
                f.setStyleSheet(f"background-color: {c}; border-radius: 1px;")
        if channel >= 0 and channel < len(self._vu_analog_widgets):
            self._vu_analog_widgets[channel].set_value(value)

    def _update_vu(self):
        """Simulierte Aussteuerung L/R (7 LEDs); Senderstärke aus Bitrate."""
        if not self._playing:
            return
        for ch in (0, 1):
            # Wert aus Bar lesen oder neu berechnen (wir speichern nicht in Bar, nutzen Zufall)
            w = getattr(self, f"_vu_val_{ch}", 50)
            w = min(100, max(0, w + random.randint(-8, 12)))
            setattr(self, f"_vu_val_{ch}", w)
            self._set_led_strip(ch, w)

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
                # Radio SAW: Sender-/Stream-Namen („Radio SAW“, „Live“, „Simulcast“) gelten nicht als echte Titel
                is_saw_url = "stream.radiosaw.de" in url
                title_val = (meta.get("title") or "").strip()
                saw_station_name_only = is_saw_url and (
                    not title_val or title_val.upper() in ("LIVE", "RADIO SAW", "RADIO SAW SIMULCAST")
                    or "simulcast" in title_val.lower() or title_val.lower().startswith(("radio saw", "saw "))
                )
                has_real_meta = (title_val not in ("", "Live") and not saw_station_name_only) or (meta.get("artist") or meta.get("song"))
                if not has_real_meta:
                    icy = _fetch_icy_metadata_direct(url)
                    if icy and ((icy.get("title") or icy.get("artist") or icy.get("song"))):
                        meta = icy
                    if is_saw_url and not (meta.get("artist") or meta.get("song")) and (not (meta.get("title") or "").strip() or saw_station_name_only):
                        meta["metadata_unsupported"] = True
                        meta["title"] = ""
                        meta["song"] = ""
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
    
    def resizeEvent(self, event):
        """Bei Größenänderung X-Button neu positionieren."""
        super().resizeEvent(event)
        self._position_close_button()
    
    def showEvent(self, event):
        """Fenstertitel früh setzen, damit Wayfire-Regel (DSI-1/TFT) greift."""
        self.setWindowTitle(WINDOW_TITLE)
        super().showEvent(event)
        QTimer.singleShot(0, self._position_close_button)
        self._setup_screenshot_shortcut()
        QTimer.singleShot(0, self._move_to_dsi_display)
        # Uhr- und Backend-Timer erst 500 ms nach show starten (QBasicTimer nur im Objekt-Thread)
        QTimer.singleShot(500, self._startMainTimersSlot)
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
