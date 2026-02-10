#!/usr/bin/env python3
"""
PI-Installer DSI Radio – Standalone PyQt6-App für Freenove 4,3" DSI.
20 Favoriten-Slots, Senderliste (Radio-Browser-API), Klavierlack-Design, Wechseldesigns.
Wayfire: Fenstertitel „PI-Installer DSI Radio“ → start_on_output DSI-1 (TFT).
"""

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
from PyQt6.QtCore import Qt, QTimer, QByteArray, QRectF, QBuffer, QIODevice, QMimeData
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush, QColor, QImage
from math import pi, cos, sin

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
THEME_FILE = os.path.join(CONFIG_DIR, "theme.txt")
FAVORITES_PER_PAGE = 9

try:
    from stations import RADIO_STATIONS
except ImportError:
    RADIO_STATIONS = [
        {"id": "einslive", "name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "wdr2", "name": "WDR 2", "stream_url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "logo_url": "", "region": "NRW", "genre": "Pop"},
        {"id": "dlf", "name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "logo_url": "", "region": "Bundesweit", "genre": "Info"},
    ]


def _find_player() -> Optional[str]:
    for cmd in ("cvlc", "mpv", "mpg123"):
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=2)
            return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _find_audio_sink() -> Optional[str]:
    """Findet das richtige PulseAudio-Sink (nicht HDMI-1-1, bevorzuge Gehäuse-Lautsprecher)."""
    try:
        # Prüfe ob pactl verfügbar ist (PipeWire-Pulse oder PulseAudio)
        if subprocess.run(["which", "pactl"], capture_output=True).returncode != 0:
            return None
        
        # Liste aller Sinks abrufen
        result = subprocess.run(
            ["pactl", "list", "short", "sinks"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            non_hdmi_sinks = []
            hdmi1_2_sinks = []  # HDMI-1-2 (Hauptbildschirm) - 107c706400
            hdmi1_1_sinks = []  # HDMI-1-1 (sollte vermieden werden) - 107c701400
            all_sinks = []
            
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    sink_id = parts[0]  # ID ist in der ersten Spalte
                    sink_name = parts[1]  # Name ist in der zweiten Spalte
                    all_sinks.append(sink_name)
                    sink_lower = sink_name.lower()
                    
                    # Bevorzuge nicht-HDMI-Geräte (Gehäuse-Lautsprecher, Headphones, etc.)
                    if "hdmi" not in sink_lower:
                        non_hdmi_sinks.append(sink_name)
                    # Prüfe auf HDMI-1-2 (Hauptbildschirm) - erkenne an verschiedenen Mustern
                    # 107c706400 = HDMI-1-2 (Hauptbildschirm, sollte verwendet werden)
                    elif ("107c706400" in sink_name or "platform-107c706400" in sink_name or
                          "hdmi-1-2" in sink_lower or "hdmi1-2" in sink_lower or 
                          "hdmi_a_2" in sink_lower):
                        # HDMI-1-2 (Hauptbildschirm) - zweite Priorität
                        hdmi1_2_sinks.append(sink_name)
                    # Prüfe auf HDMI-1-1 (sollte vermieden werden)
                    # 107c701400 = HDMI-1-1 (sollte vermieden werden)
                    elif ("107c701400" in sink_name or "platform-107c701400" in sink_name or
                          "hdmi-1-1" in sink_lower or "hdmi1-1" in sink_lower or 
                          "hdmi_a_1" in sink_lower):
                        # HDMI-1-1 - niedrigste Priorität (sollte vermieden werden)
                        hdmi1_1_sinks.append(sink_name)
            
            # Priorität: 1. Nicht-HDMI, 2. HDMI-1-2 (107c706400), 3. Andere HDMI, 4. HDMI-1-1 (107c701400)
            selected_sink = None
            if non_hdmi_sinks:
                selected_sink = non_hdmi_sinks[0]
            elif hdmi1_2_sinks:
                # HDMI-1-2 (Hauptbildschirm) - bevorzugt verwenden
                selected_sink = hdmi1_2_sinks[0]
            elif all_sinks:
                # Alle anderen Sinks (außer HDMI-1-1)
                for sink in all_sinks:
                    if sink not in hdmi1_1_sinks:
                        selected_sink = sink
                        break
                # Fallback: Erstes verfügbares Sink (auch wenn es HDMI-1-1 ist)
                if not selected_sink:
                    selected_sink = all_sinks[0]
            
            # Debug: Logge gefundenen Sink
            try:
                debug_file = os.path.join(CONFIG_DIR, "audio_sink_selected.log")
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: Ausgewählter Sink: {selected_sink}\n")
                    f.write(f"  Verfügbare Sinks: {len(all_sinks)} (HDMI-1-2: {len(hdmi1_2_sinks)}, HDMI-1-1: {len(hdmi1_1_sinks)}, Non-HDMI: {len(non_hdmi_sinks)})\n")
            except Exception:
                pass
            
            return selected_sink
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
    try:
        req = urllib.request.Request(
            f"{BACKEND_BASE}/api/radio/stream-metadata?url={urllib.request.quote(url, safe='')}",
            headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"},
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.load(resp)
            if isinstance(data, dict):
                # Entferne "status"-Feld aus API-Antwort (ist kein Metadaten-Feld)
                if "status" in data:
                    del data["status"]
                
                # Debug: Metadaten in Datei schreiben für Diagnose
                try:
                    debug_file = os.path.join(CONFIG_DIR, "metadata_debug.json")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        json.dump({"url": url, "metadata": data, "timestamp": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                return data
    except Exception as e:
        # Debug: Fehler in Datei schreiben
        try:
            debug_file = os.path.join(CONFIG_DIR, "metadata_error.log")
            with open(debug_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()}: {type(e).__name__}: {str(e)}\n")
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
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read()
    except Exception:
        pass
    # Fallback: Direkt laden mit Wikimedia-konformem User-Agent
    try:
        ua = "PI-Installer/1.0 (Radio logo; +https://github.com)" if ("wikipedia.org" in url or "wikimedia.org" in url) else "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read()
    except Exception:
        return None


def _fetch_stations_search(name: str = "") -> List[Dict[str, Any]]:
    try:
        url = f"{BACKEND_BASE}/api/radio/stations/search?country=Germany&limit=200"
        if name.strip():
            url += "&name=" + urllib.request.quote(name.strip())
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            if isinstance(data, dict) and "stations" in data:
                return data["stations"]
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

    def __init__(self, parent=None, signal_mode: bool = False):
        super().__init__(parent)
        self._value = 0
        self._signal_mode = signal_mode
        self.setFixedSize(64, 64)
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
    """Senderliste: Suchen, auswählen, zu Favoriten (max 20)."""

    def __init__(self, parent: Optional[QMainWindow], current_favorites: List[Dict[str, Any]], theme_name: str = "Klavierlack"):
        super().__init__(parent)
        self.setWindowTitle("Senderliste – Favoriten wählen")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(THEMES.get(theme_name, STYLE_KLAVIERLACK))
        self._current_favorites = list(current_favorites)
        self._add_station = None  # (parent will read via get_add_station)
        layout = QVBoxLayout(self)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Sender suchen (z. B. 1Live, NDR, Bayern…)")
        self._search.setMinimumHeight(44)
        layout.addWidget(self._search)
        btn_row = QHBoxLayout()
        search_btn = QPushButton("Suchen")
        search_btn.setMinimumHeight(48)
        search_btn.clicked.connect(self._do_search)
        self._search.returnPressed.connect(self._do_search)
        btn_row.addWidget(search_btn)
        add_btn = QPushButton("Zu Favoriten (max 20)")
        add_btn.setMinimumHeight(48)
        add_btn.clicked.connect(self._add_to_favorites)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)
        self._list = QListWidget()
        self._list.setMinimumHeight(280)
        layout.addWidget(self._list)
        close_btn = QPushButton("Schließen")
        close_btn.setMinimumHeight(48)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self._do_search()

    def _do_search(self):
        self._list.clear()
        self._list.addItem(QListWidgetItem("Suche läuft…"))
        name = self._search.text().strip()
        def do():
            try:
                stations = _fetch_stations_search(name)
                def apply():
                    self._list.clear()
                    if not stations or len(stations) == 0:
                        # Fallback: Standardliste anzeigen
                        for s in RADIO_STATIONS[:50]:
                            item = QListWidgetItem(s.get("name", "") + " – " + ((s.get("stream_url", ""))[:50] + "…" if len(s.get("stream_url", "")) > 50 else s.get("stream_url", "")))
                            item.setData(Qt.ItemDataRole.UserRole, {"name": s.get("name"), "url": s.get("stream_url"), "favicon": s.get("logo_url"), "state": s.get("region"), "tags": s.get("genre")})
                            self._list.addItem(item)
                        if not self._list.count():
                            self._list.addItem(QListWidgetItem("Keine Sender gefunden. Backend erreichbar?"))
                        return
                    # API-Senderliste anzeigen
                    for s in stations:
                        if not isinstance(s, dict):
                            continue
                        station_name = s.get("name", "Unbekannt")
                        station_url = s.get("url", "")
                        display_text = station_name
                        if station_url:
                            display_text += " – " + (station_url[:50] + "…" if len(station_url) > 50 else station_url)
                        item = QListWidgetItem(display_text)
                        item.setData(Qt.ItemDataRole.UserRole, s)
                        self._list.addItem(item)
                    if self._list.count() == 0:
                        self._list.addItem(QListWidgetItem("Keine Sender gefunden. Versuchen Sie eine andere Suche."))
                QTimer.singleShot(0, apply)
            except Exception as e:
                def apply_error():
                    self._list.clear()
                    self._list.addItem(QListWidgetItem(f"Fehler bei der Suche: {str(e)}"))
                    # Fallback: Standardliste anzeigen
                    for s in RADIO_STATIONS[:20]:
                        item = QListWidgetItem(s.get("name", "") + " – " + ((s.get("stream_url", ""))[:50] + "…" if len(s.get("stream_url", "")) > 50 else s.get("stream_url", "")))
                        item.setData(Qt.ItemDataRole.UserRole, {"name": s.get("name"), "url": s.get("stream_url"), "favicon": s.get("logo_url"), "state": s.get("region"), "tags": s.get("genre")})
                        self._list.addItem(item)
                QTimer.singleShot(0, apply_error)
        threading.Thread(target=do, daemon=True).start()

    def _add_to_favorites(self):
        row = self._list.currentRow()
        if row < 0:
            return
        item = self._list.item(row)
        s = item.data(Qt.ItemDataRole.UserRole)
        if not s or len(self._current_favorites) >= FAVORITES_MAX:
            if len(self._current_favorites) >= FAVORITES_MAX:
                QMessageBox.information(self, "Favoriten", f"Maximal {FAVORITES_MAX} Sender.")
            return
        name = (s.get("name") or "").strip()
        url = (s.get("url") or "").strip()
        if not url:
            return
        fav = {"id": "rb_" + str(hash(url) % 10**8), "name": name, "stream_url": url, "logo_url": (s.get("favicon") or "").strip() or "", "region": s.get("state") or "", "genre": s.get("tags") or ""}
        if any(f.get("stream_url") == url for f in self._current_favorites):
            return
        self._current_favorites.append(fav)
        save_favorites(self._current_favorites)
        self._add_station = fav
        QMessageBox.information(self, "Favoriten", f"'{name}' zu Favoriten hinzugefügt.")
        self.parent()._reload_favorites() if self.parent() else None
        self.parent()._rebuild_station_buttons() if hasattr(self.parent(), "_rebuild_station_buttons") else None

    def get_added_station(self):
        return getattr(self, "_add_station", None)


class DsiRadioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._player_cmd = _find_player()
        self._process: Optional[subprocess.Popen] = None
        self._favorites: List[Dict[str, Any]] = load_favorites()
        self._current_station = self._favorites[0] if self._favorites else {}
        self._playing = False
        self._metadata: dict = {}
        self._theme = load_theme()
        self._favorites_page = 0
        self._metadata_timer = QTimer(self)
        self._metadata_timer.timeout.connect(self._poll_metadata)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._vu_timer = QTimer(self)
        self._vu_timer.timeout.connect(self._update_vu)
        self._build_ui()

    def _reload_favorites(self):
        self._favorites = load_favorites()
        if self._favorites and not any(s.get("id") == self._current_station.get("id") for s in self._favorites):
            self._current_station = self._favorites[0]

    def _build_ui(self):
        self._apply_theme(self._theme)
        central = QWidget()
        self.setCentralWidget(central)
        main_v = QVBoxLayout(central)
        main_v.setContentsMargins(10, 6, 6, 8)
        main_v.setSpacing(8)

        # Radioanzeige oben: vollständige Breite mit Logo oben links und 3D-Effekt
        card = QFrame()
        card.setObjectName("display")
        card.setStyleSheet("background: transparent; border: none;")
        
        # Schwarzer Rahmen ohne 3D-Effekt (maximal 5 Pixel breit, oben/links/rechts am Rand)
        black_frame = QFrame()
        black_frame.setStyleSheet("""
            background: #0c0c0c;
            border-top: 5px solid #000000;
            border-left: 5px solid #000000;
            border-right: 5px solid #000000;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            padding: 5px;
        """)
        black_frame_layout = QVBoxLayout(black_frame)
        black_frame_layout.setContentsMargins(5, 5, 5, 5)
        black_frame_layout.setSpacing(0)
        
        # Weißes Display mit Logo links, Text rechts (um 20 Pixel höher: 160 statt 140, kein Rahmen)
        green_display = QFrame()
        green_display.setStyleSheet("background: #ffffff; border: none; border-radius: 0px; padding: 6px;")
        green_display.setMaximumHeight(160)
        green_display_layout = QVBoxLayout(green_display)
        green_display_layout.setContentsMargins(6, 6, 6, 6)
        green_display_layout.setSpacing(0)
        
        # Hauptbereich: Logo links, Text rechts
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(8)
        
        # Logo-Bereich links (proportional, ohne Rahmen, nicht abgeschnitten)
        logo_container = QVBoxLayout()
        logo_container.setSpacing(2)
        self._logo_label = QLabel()
        self._logo_label.setMaximumSize(100, 100)
        self._logo_label.setMinimumSize(60, 60)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("background-color: transparent; border: none; color: #0f172a; font-size: 20px;")
        self._logo_label.setText("…")
        self._logo_label.setScaledContents(False)  # Nicht strecken/dehnen, Proportionen beibehalten
        logo_container.addWidget(self._logo_label)
        # Platz für Audioqualität unter Logo (später)
        self._quality_label = QLabel("")
        self._quality_label.setFont(QFont("Sans", 9))
        self._quality_label.setStyleSheet("color: #0f172a; border: none;")
        self._quality_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._quality_label.setMaximumHeight(16)
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
        text_container.addWidget(self._station_label)
        
        # Musikrichtung
        self._genre_label = QLabel(self._current_station.get("genre", ""))
        self._genre_label.setFont(QFont("Sans", 14))
        self._genre_label.setStyleSheet("color: #0f172a; border: none;")
        text_container.addWidget(self._genre_label)
        
        # Titel
        self._title_label = QLabel("")
        self._title_label.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self._title_label.setStyleSheet("color: #0f172a; border: none;")
        self._title_label.setWordWrap(True)
        text_container.addWidget(self._title_label)
        
        # Interpret
        self._artist_label = QLabel("")
        self._artist_label.setFont(QFont("Sans", 13))
        self._artist_label.setStyleSheet("color: #0f172a; border: none;")
        self._artist_label.setWordWrap(True)
        text_container.addWidget(self._artist_label)
        
        # Laufende Sendung
        self._show_label = QLabel("")
        self._show_label.setFont(QFont("Sans", 11))
        self._show_label.setStyleSheet("color: #0f172a; border: none;")
        self._show_label.setWordWrap(True)
        text_container.addWidget(self._show_label)
        
        text_container.addStretch()
        content_row.addLayout(text_container, 1)
        
        green_display_layout.addLayout(content_row, 1)
        black_frame_layout.addWidget(green_display, 0)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card_layout.addWidget(black_frame)
        
        # X-Button oben rechts auf dem Rahmen (ohne Rahmen, absolut positioniert)
        self._close_btn = QPushButton("✕", card)
        self._close_btn.setFixedSize(18, 18)
        self._close_btn.setToolTip("Radio beenden")
        self._close_btn.clicked.connect(self.close)
        self._close_btn.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            border: none; 
            background: transparent; 
            color: #ffffff; 
        """)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.raise_()  # Über anderen Widgets
        
        main_v.addWidget(card)
        
        # Restliche UI-Elemente in horizontalem Layout
        main_h = QHBoxLayout()
        main_h.setSpacing(8)
        left = QWidget()
        layout = QVBoxLayout(left)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Uhr: nur 2 Pixel oberhalb und unterhalb der Anzeige, Bereich kompakt
        clock_font = QFont("Sans", 14, QFont.Weight.Bold)
        self._clock_label = QLabel()
        self._clock_label.setFont(clock_font)
        self._clock_label.setStyleSheet("color: #94a3b8; border: none;")
        self._clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_bar = QFrame()
        clock_bar.setStyleSheet("background: transparent; border: none;")
        clock_layout = QVBoxLayout(clock_bar)
        clock_layout.setContentsMargins(0, 2, 0, 2)
        clock_layout.setSpacing(0)
        clock_layout.addWidget(self._clock_label)
        layout.addWidget(clock_bar)
        self._update_clock()

        # VU L/R + Signal: LED oder Analog; Schiebeschalter (Digital/Analog) am rechten Rand
        self._vu_mode = "led"
        self._vu_leds: List[List[QFrame]] = []
        self._vu_analog_widgets: List[AnalogGaugeWidget] = []
        vu_row = QHBoxLayout()
        vu_row.setSpacing(8)
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
        for ch, lab in enumerate(["L", "R", "Signal"]):
            if ch == 1:
                analog_layout.addSpacing(24)
            elif ch == 2:
                analog_layout.addSpacing(48)
            col = QVBoxLayout()
            lbl = QLabel(lab)
            lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            col.addWidget(lbl)
            gauge = AnalogGaugeWidget(self, signal_mode=(ch == 2))
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

        # Senderliste + Play/Pause
        row = QHBoxLayout()
        list_btn = QPushButton("📻 Senderliste")
        list_btn.setMinimumHeight(48)
        list_btn.setObjectName("play")
        list_btn.clicked.connect(self._open_station_list)
        row.addWidget(list_btn)
        self._play_btn = QPushButton("▶ Abspielen")
        self._play_btn.setMinimumHeight(52)
        self._play_btn.setObjectName("play")
        self._play_btn.clicked.connect(self._toggle_play)
        row.addWidget(self._play_btn)
        if not self._player_cmd:
            self._play_btn.setEnabled(False)
        layout.addLayout(row)

        hint = QLabel("Kein Ton? Einstellungen → Sound → Ausgabegerät: Gehäuse-Lautsprecher.")
        hint.setStyleSheet("color: #64748b; font-size: 9px;")
        hint.setMaximumHeight(20)
        layout.addWidget(hint)
        
        # Audio-Ausgabegerät beim Start prüfen
        QTimer.singleShot(1000, self._check_audio_output)

        main_h.addWidget(left, 1)
        main_v.addLayout(main_h)

        portrait = os.environ.get("PI_INSTALLER_DSI_PORTRAIT", "").lower() in ("1", "true", "yes")
        self.setMinimumSize(380, 320)
        (w, h) = (480, 800) if portrait else (800, 480)
        self.resize(w, h)
        self._update_logo()
        self._update_senderinfo()
        self._clock_timer.start(CLOCK_INTERVAL_MS)

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
        sorted_fav = sorted(self._favorites, key=lambda s: (s.get("name") or "").lower())
        start = self._favorites_page * FAVORITES_PER_PAGE
        page_fav = sorted_fav[start : start + FAVORITES_PER_PAGE]
        cols = 3
        for i, s in enumerate(page_fav):
            b = QPushButton(_button_label(s.get("name", "?")))
            b.setProperty("station_id", s.get("id"))
            b.setCheckable(True)
            b.setChecked(s.get("id") == self._current_station.get("id"))
            b.setMinimumHeight(48)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
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
        """Lautstärke des aktiven Kanals: PulseAudio oder ALSA setzen."""
        pct = max(0, min(100, value))
        # Prüfe ob PulseAudio verfügbar ist
        has_pulseaudio = subprocess.run(["which", "pactl"], capture_output=True).returncode == 0
        
        if has_pulseaudio:
            # PulseAudio (betrifft Standard-Ausgabe und damit den Player)
            try:
                r = subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{pct}%"],
                    timeout=2,
                    capture_output=True,
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
        genre = self._current_station.get("genre") or ""
        self._genre_label.setText(genre)

    def _on_station(self, st: dict):
        # Automatisch abspielen wie bei einem richtigen Radio
        was_playing = self._playing
        self._stop_stream()
        self._current_station = st
        for b in self._station_buttons:
            b.setChecked(b.property("station_id") == st.get("id"))
        self._station_label.setText(st.get("name", "—"))
        self._update_senderinfo()
        self._title_label.setText("")
        self._artist_label.setText("")
        self._show_label.setText("")
        self._quality_label.setText("")
        self._metadata = {}
        self._update_logo()
        # Automatisch starten (wie bei einem richtigen Radio)
        self._start_stream()

    def _update_logo(self):
        url = self._current_station.get("logo_url") or ""
        data = _fetch_logo(url) if url else None
        if data:
            pix = QPixmap()
            pix.loadFromData(QByteArray(data))
            if not pix.isNull():
                # Logo proportional skalieren, maximal 100x100, Proportionen beibehalten
                max_size = 100
                original_width = pix.width()
                original_height = pix.height()
                
                # Berechne Skalierung, damit Logo nicht abgeschnitten wird
                if original_width > 0 and original_height > 0:
                    scale = min(max_size / original_width, max_size / original_height)
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    
                    # Skaliere mit SmoothTransformation, Proportionen beibehalten
                    scaled_pix = pix.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self._logo_label.setPixmap(scaled_pix)
                    self._logo_label.setText("")  # Text löschen wenn Pixmap gesetzt wird
                else:
                    self._logo_label.setPixmap(QPixmap())
                    self._logo_label.setText((self._current_station.get("name") or "?")[:2])
            else:
                self._logo_label.setPixmap(QPixmap())  # Pixmap löschen
                self._logo_label.setText((self._current_station.get("name") or "?")[:2])
        else:
            self._logo_label.setPixmap(QPixmap())  # Pixmap löschen
            self._logo_label.setText((self._current_station.get("name") or "?")[:2])

    def _start_stream(self):
        # Stelle sicher, dass kein alter Stream läuft
        if self._process:
            # Prozess läuft noch - zuerst stoppen
            self._stop_stream()
            # Kurz warten, damit Prozess beendet wird
            import time
            time.sleep(0.3)
        
        if not self._player_cmd:
            return
        
        url = self._current_station.get("stream_url", "")
        if not url:
            return
        
        # Audio-Ausgabegerät finden (nicht HDMI-1-1, bevorzuge Gehäuse-Lautsprecher)
        audio_sink = _find_audio_sink()
        has_pulseaudio = subprocess.run(["which", "pactl"], capture_output=True).returncode == 0
        
        # Falls kein Sink gefunden wurde, verwende Standard-Sink
        if not audio_sink and has_pulseaudio:
            try:
                result = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    audio_sink = result.stdout.strip()
            except Exception:
                pass
        
        # Debug: Audio-Sink-Info
        debug_info = {"player": self._player_cmd, "audio_sink": audio_sink, "has_pulseaudio": has_pulseaudio, "url": url}
        
        if self._player_cmd == "cvlc":
            cmd = ["cvlc", "--no-video", "--play-and-exit"]
            if has_pulseaudio:
                if audio_sink:
                    # VLC: PulseAudio-Sink explizit setzen
                    cmd.extend(["--aout=pulse", f"--pulse-audio-device={audio_sink}"])
                else:
                    # Fallback: PulseAudio ohne explizites Gerät
                    cmd.append("--aout=pulse")
            else:
                # Kein PulseAudio: ALSA verwenden
                # Für Freenove: Gehäuse-Lautsprecher könnte über HDMI verfügbar sein
                # Versuche HDMI-1-2 (Hauptbildschirm) statt HDMI-1-1 zu verwenden
                # ALSA-Gerät: hw:1,0 für vc4hdmi1 (HDMI-1-2) oder hw:0,0 für vc4hdmi0 (HDMI-1-1)
                # Standard: hw:1,0 (HDMI-1-2, Hauptbildschirm)
                cmd.extend(["--aout=alsa", "--alsa-audio-device=hw:1,0"])
            cmd.append(url)
        elif self._player_cmd == "mpv":
            cmd = ["mpv", "--no-video", "--no-terminal"]
            if has_pulseaudio:
                if audio_sink:
                    # mpv: PulseAudio-Sink explizit setzen
                    cmd.extend([f"--audio-device=pulse/{audio_sink}"])
                else:
                    # Fallback: PulseAudio ohne explizites Gerät
                    cmd.append("--audio-device=pulse")
            else:
                # Kein PulseAudio: ALSA verwenden
                cmd.append("--audio-device=alsa")
            cmd.append(url)
        else:
            # mpg123 nutzt ALSA direkt - PulseAudio-Sink als ALSA-Gerät setzen
            cmd = ["mpg123", "-q"]
            if audio_sink:
                # Versuche ALSA-Gerät für PulseAudio-Sink zu finden
                try:
                    result = subprocess.run(
                        ["pactl", "list", "short", "sinks"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        # Finde ALSA-Gerät für dieses Sink
                        for line in result.stdout.strip().split("\n"):
                            if audio_sink in line:
                                parts = line.split("\t")
                                if len(parts) >= 1:
                                    # ALSA-Gerät ist oft in der Form "alsa_output.xxx"
                                    alsa_name = parts[0] if "." in parts[0] else None
                                    if alsa_name:
                                        cmd.extend(["-a", alsa_name])
                                        debug_info["alsa_device"] = alsa_name
                except Exception:
                    pass
            cmd.append(url)
        
        debug_info["command"] = " ".join(cmd)
        
        try:
            # Debug: Audio-Sink in Datei schreiben (vor Start)
            try:
                debug_file = os.path.join(CONFIG_DIR, "audio_sink.log")
                with open(debug_file, "a", encoding="utf-8") as f:
                    import json
                    f.write(f"{datetime.now().isoformat()}: {json.dumps(debug_info, ensure_ascii=False)}\n")
            except Exception:
                pass
            
            # Player starten - stderr nicht verwerfen für Debugging
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,  # Für Debugging behalten
                stdin=subprocess.DEVNULL
            )
            
            # Prüfe ob Prozess läuft (nach kurzer Wartezeit)
            import time
            time.sleep(0.5)
            if self._process.poll() is not None:
                # Prozess ist bereits beendet - Fehler
                stderr_output = self._process.stderr.read().decode("utf-8", errors="ignore") if self._process.stderr else ""
                raise Exception(f"Player beendet sich sofort. Exit-Code: {self._process.returncode}, Fehler: {stderr_output[:200]}")
            
            self._playing = True
            self._play_btn.setText("⏸ Pause")
            self._title_label.setText("Live …")
            self._vu_val_0 = 50
            self._vu_val_1 = 50
            self._metadata_timer.start(METADATA_INTERVAL_MS)
            self._poll_metadata()
            self._vu_timer.start(50)
            
        except Exception as e:
            self._playing = False
            self._title_label.setText("Streamfehler")
            # Debug: Fehler in Datei schreiben
            try:
                debug_file = os.path.join(CONFIG_DIR, "stream_error.log")
                with open(debug_file, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()}: Stream-Start fehlgeschlagen: {type(e).__name__}: {str(e)}\n")
                    f.write(f"  Command: {' '.join(cmd)}\n")
                    f.write(f"  Audio-Sink: {audio_sink or 'None'}\n")
            except Exception:
                pass

    def _stop_stream(self):
        self._metadata_timer.stop()
        self._vu_timer.stop()
        for ch in (0, 1, 2):
            self._set_led_strip(ch, 0)
        if self._process:
            try:
                # Prozess beenden - zuerst terminate, dann kill falls nötig
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Prozess reagiert nicht - kill
                    self._process.kill()
                    self._process.wait(timeout=1)
            except Exception:
                # Fallback: kill direkt
                try:
                    self._process.kill()
                    self._process.wait(timeout=1)
                except Exception:
                    pass
            self._process = None
        
        # Zusätzlich: Alle Player-Prozesse beenden (falls Prozess-Handle verloren wurde)
        try:
            # Beende alle Player-Prozesse, die Streams abspielen
            for player_cmd in ("cvlc", "mpv", "mpg123"):
                # Versuche zuerst mit der aktuellen Stream-URL
                if self._current_station and self._current_station.get("stream_url"):
                    url_part = self._current_station.get("stream_url", "")[:50]
                    subprocess.run(["pkill", "-f", f"{player_cmd}.*{url_part}"], 
                                  timeout=1, capture_output=True)
                # Fallback: Beende alle Player-Prozesse dieses Typs (falls URL nicht verfügbar)
                subprocess.run(["pkill", "-9", "-f", f"{player_cmd}.*--no-video"], 
                              timeout=1, capture_output=True)
        except Exception:
            pass
        
        # Zusätzlich: Alle PulseAudio/PipeWire Sink-Inputs beenden (falls Prozess-Handle verloren wurde)
        try:
            if subprocess.run(["which", "pactl"], capture_output=True).returncode == 0:
                # Liste aller Sink-Inputs abrufen und beenden
                result = subprocess.run(
                    ["pactl", "list", "short", "sink-inputs"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            parts = line.split("\t")
                            if len(parts) >= 1:
                                sink_input_id = parts[0]
                                # Prüfe ob es ein VLC/mpv/mpg123 Input ist
                                sink_info = subprocess.run(
                                    ["pactl", "list", "sink-inputs"],
                                    capture_output=True,
                                    text=True,
                                    timeout=2
                                )
                                if sink_info.returncode == 0:
                                    # Suche nach VLC/mpv/mpg123 in der Ausgabe
                                    if "VLC" in sink_info.stdout or "mpv" in sink_info.stdout or "mpg123" in sink_info.stdout:
                                        subprocess.run(["pactl", "kill-sink-input", sink_input_id], 
                                                      timeout=1, capture_output=True)
        except Exception:
            pass
        
        # Stelle sicher, dass _process auf None gesetzt ist
        self._process = None
        self._playing = False

    def _apply_metadata(self, meta: dict):
        # Prüfe ob Stream noch läuft (kann sich zwischen Aufruf und Anzeige geändert haben)
        # Wichtig: Diese Funktion wird aus dem UI-Thread aufgerufen, daher sicher
        if not self._playing:
            # Stream läuft nicht mehr - Metadaten nicht anwenden
            return
        
        # Stelle sicher, dass UI initialisiert ist
        if not hasattr(self, "_title_label") or not self._title_label:
            # UI noch nicht initialisiert - Metadaten später anwenden
            QTimer.singleShot(100, lambda m=meta: self._apply_metadata(m))
            return
        
        # Metadaten setzen
        self._metadata = meta
        show = (meta.get("show") or meta.get("server_name") or "").strip()
        title = (meta.get("title") or "").strip()
        artist = (meta.get("artist") or "").strip()
        song = (meta.get("song") or "").strip()
        bitrate = meta.get("bitrate")
        
        # Debug: Metadaten in Datei schreiben (immer, für Diagnose)
        try:
            debug_file = os.path.join(CONFIG_DIR, "metadata_applied.json")
            debug_data = {
                "show": show,
                "title": title,
                "artist": artist,
                "song": song,
                "bitrate": bitrate,
                "timestamp": datetime.now().isoformat(),
                "raw_meta": meta,
                "playing": self._playing,
                "station": self._current_station.get("name", "Unknown")
            }
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        
        # Titel anzeigen - immer aktualisieren wenn Metadaten vorhanden
        # Prüfe zuerst ob Titel vorhanden ist (auch wenn es nur "1LIVE" ist)
        title_to_show = ""
        if title and title.strip():
            title_upper = title.strip().upper()
            # Zeige Titel an, auch wenn es nur der Sendername ist (z.B. "1LIVE")
            # Nur "LIVE" ohne weitere Info wird übersprungen
            if title_upper != "LIVE" or artist or song:
                title_to_show = title[:50] + ("…" if len(title) > 50 else "")
        
        if not title_to_show and (artist or song):
            # Kein Titel, aber Artist oder Song vorhanden
            if artist and song:
                combined = f"{artist} - {song}"
                title_to_show = combined[:50] + ("…" if len(combined) > 50 else "")
            elif artist:
                title_to_show = artist[:50] + ("…" if len(artist) > 50 else "")
            elif song:
                title_to_show = song[:50] + ("…" if len(song) > 50 else "")
        
        if title_to_show:
            self._title_label.setText(title_to_show)
        else:
            # Keine Metadaten vorhanden, aber Stream läuft
            current_text = self._title_label.text()
            if current_text == "Streamfehler" or not current_text or current_text == "":
                self._title_label.setText("Live …")
        
        # Interpret anzeigen
        if artist:
            self._artist_label.setText(artist[:50] + ("…" if len(artist) > 50 else ""))
        elif song and not artist:
            # Falls nur Song vorhanden ist, als Artist anzeigen
            self._artist_label.setText(song[:50] + ("…" if len(song) > 50 else ""))
        else:
            self._artist_label.setText("")
        
        # Laufende Sendung anzeigen
        if show:
            self._show_label.setText("Sendung: " + show[:50] + ("…" if len(show) > 50 else ""))
        else:
            self._show_label.setText("")
        
        # Audioqualität anzeigen
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
        """10 LEDs: Index 0=unten (grün), 9=oben (rot). Anzeige maximal eingestellte Lautstärke."""
        raw = max(0, min(100, value))
        vol = getattr(self, "_volume_slider", None)
        max_val = vol.value() if vol else 100
        value = min(raw, max_val)
        if channel >= 0 and channel < len(self._vu_leds):
            lit = min(10, int((value / 100) * 10.99))
            off, green, yellow, red_c = "#1e293b", "#22c55e", "#eab308", "#dc2626"
            for i, f in enumerate(self._vu_leds[channel]):
                on = i < lit
                if i < 6:
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
        url = self._current_station.get("stream_url", "")
        if not url or not self._playing:
            return
        def do():
            try:
                # Debug: Backend-Verbindung testen
                backend_reachable = False
                try:
                    import urllib.request
                    test_req = urllib.request.Request(
                        f"{BACKEND_BASE}/api/radio/stream-metadata?url={urllib.request.quote(url, safe='')}",
                        headers={"User-Agent": "PI-Installer-DSI-Radio/1.0"}
                    )
                    test_resp = urllib.request.urlopen(test_req, timeout=5)
                    backend_reachable = test_resp.status == 200
                except Exception as e:
                    try:
                        debug_file = os.path.join(CONFIG_DIR, "backend_check.log")
                        with open(debug_file, "a", encoding="utf-8") as f:
                            f.write(f"{datetime.now().isoformat()}: Backend nicht erreichbar ({BACKEND_BASE}): {type(e).__name__}: {str(e)}\n")
                    except Exception:
                        pass
                
                if not backend_reachable:
                    # Backend nicht erreichbar - leere Metadaten
                    QTimer.singleShot(0, lambda: self._apply_metadata({}))
                    return
                
                # Metadaten abrufen
                meta_raw = _fetch_metadata(url)
                # Prüfe ob Metadaten gültig sind
                if not isinstance(meta_raw, dict):
                    meta_raw = {}
                
                # Entferne "status"-Feld falls vorhanden (ist kein Metadaten-Feld)
                meta = {k: v for k, v in meta_raw.items() if k != "status"}
                
                # Debug: Metadaten-Ergebnis loggen
                try:
                    debug_file = os.path.join(CONFIG_DIR, "metadata_poll.log")
                    with open(debug_file, "a", encoding="utf-8") as f:
                        import json
                        f.write(f"{datetime.now().isoformat()}: Metadaten abgerufen: {json.dumps(meta, ensure_ascii=False)}\n")
                        f.write(f"  Playing: {self._playing}, Station: {self._current_station.get('name', 'Unknown')}\n")
                except Exception:
                    pass
                
                # Metadaten anwenden (direkt im UI-Thread)
                # Wichtig: Kopie der Metadaten erstellen für Thread-Sicherheit
                meta_copy = dict(meta)  # Kopie erstellen für Thread-Sicherheit
                playing_state = self._playing  # Zustand speichern
                station_name = self._current_station.get("name", "Unknown")
                
                def apply_meta():
                    # Debug: Vor dem Anwenden
                    try:
                        debug_file = os.path.join(CONFIG_DIR, "metadata_apply_debug.log")
                        with open(debug_file, "a", encoding="utf-8") as f:
                            import json
                            f.write(f"{datetime.now().isoformat()}: apply_meta() aufgerufen\n")
                            f.write(f"  Playing state: {playing_state}, Current playing: {self._playing}\n")
                            f.write(f"  Station name: {station_name}, Current station: {self._current_station.get('name', 'Unknown')}\n")
                            f.write(f"  Has title_label: {hasattr(self, '_title_label')}\n")
                            f.write(f"  Meta data: {json.dumps(meta_copy, ensure_ascii=False)}\n")
                    except Exception:
                        pass
                    
                    # Prüfe nochmal ob Stream noch läuft und Station noch gleich ist
                    if playing_state and self._playing and self._current_station.get("name") == station_name:
                        try:
                            # Metadaten direkt anwenden (sind bereits im UI-Thread)
                            self._apply_metadata(meta_copy)
                        except Exception as e:
                            # Debug: Fehler beim Anwenden der Metadaten
                            try:
                                debug_file = os.path.join(CONFIG_DIR, "metadata_apply_error.log")
                                with open(debug_file, "a", encoding="utf-8") as f:
                                    f.write(f"{datetime.now().isoformat()}: Fehler beim Anwenden der Metadaten: {type(e).__name__}: {str(e)}\n")
                                    import traceback
                                    f.write(f"Traceback: {traceback.format_exc()}\n")
                            except Exception:
                                pass
                    else:
                        # Debug: Warum Metadaten nicht angewendet werden
                        try:
                            debug_file = os.path.join(CONFIG_DIR, "metadata_apply_debug.log")
                            with open(debug_file, "a", encoding="utf-8") as f:
                                f.write(f"{datetime.now().isoformat()}: Metadaten NICHT angewendet - Bedingung nicht erfüllt\n")
                                f.write(f"  playing_state={playing_state}, self._playing={self._playing}\n")
                                f.write(f"  station_name={station_name}, current_station={self._current_station.get('name', 'Unknown')}\n")
                        except Exception:
                            pass
                
                # Sofort anwenden (nicht verzögert) - QTimer.singleShot(0) führt im nächsten Event-Loop aus
                QTimer.singleShot(0, apply_meta)
                
                # Zusätzlich: Direkt anwenden falls wir bereits im UI-Thread sind
                # (QTimer.singleShot kann manchmal verzögert sein)
                try:
                    from PyQt6.QtCore import QThread
                    if QThread.currentThread() == self.thread():
                        # Wir sind bereits im UI-Thread - direkt anwenden
                        self._apply_metadata(meta_copy)
                except Exception:
                    pass
            except Exception as e:
                # Fehler beim Abrufen der Metadaten - nicht kritisch, Stream läuft weiter
                try:
                    debug_file = os.path.join(CONFIG_DIR, "metadata_error.log")
                    with open(debug_file, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()}: Metadaten-Abruf fehlgeschlagen: {type(e).__name__}: {str(e)}\n")
                        import traceback
                        f.write(f"Traceback: {traceback.format_exc()}\n")
                except Exception:
                    pass
                # Leere Metadaten anwenden (Stream läuft weiter)
                QTimer.singleShot(0, lambda: self._apply_metadata({}))
        threading.Thread(target=do, daemon=True).start()

    def _toggle_play(self):
        if self._playing:
            self._stop_stream()
            self._play_btn.setText("▶ Abspielen")
            self._title_label.setText("Pause")
        else:
            self._start_stream()

    def _position_close_button(self):
        """Positioniert den X-Button oben rechts auf dem Rahmen."""
        if hasattr(self, '_close_btn') and self._close_btn:
            # Finde das card-Widget
            card = self._close_btn.parent()
            if card:
                # Position oben rechts: 5 Pixel vom Rand (Rahmenbreite)
                x = card.width() - self._close_btn.width() - 5
                y = 5
                self._close_btn.move(x, y)
    
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
        """Prüft ob das richtige Audio-Ausgabegerät verwendet wird."""
        try:
            import subprocess
            # Prüfe ob PulseAudio verfügbar ist
            has_pulseaudio = subprocess.run(["which", "pactl"], capture_output=True).returncode == 0
            
            if not has_pulseaudio:
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
            
            # PulseAudio verfügbar - prüfe Standard-Sink
            result = subprocess.run(
                ["pactl", "info"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Prüfe Standard-Sink
                sink_result = subprocess.run(
                    ["pactl", "get-default-sink"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if sink_result.returncode == 0:
                    sink_name = sink_result.stdout.strip()
                    # Prüfe ob es ein HDMI-Audio-Gerät ist (sollte vermieden werden)
                    if "hdmi" in sink_name.lower():
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
        # X-Button positionieren nachdem alles angezeigt wurde
        QTimer.singleShot(10, self._position_close_button)
        # Screenshot-Shortcut nach dem Anzeigen einrichten
        self._setup_screenshot_shortcut()
        # Unter X11: Fenster auf DSI-1 Display verschieben
        QTimer.singleShot(100, self._move_to_dsi_display)

    def _setup_screenshot_shortcut(self):
        """F10 Tastenkürzel für Screenshot einrichten."""
        # Shortcut wird über keyPressEvent behandelt
        pass
    
    def keyPressEvent(self, event):
        """Tastendruck-Ereignisse behandeln."""
        if event.key() == Qt.Key.Key_F10:
            self._take_screenshot()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def _take_screenshot(self):
        """Erstellt einen Screenshot der Radio-App und kopiert ihn in den Zwischenspeicher."""
        try:
            # Methode 1: Versuche grab() des Fensters
            pixmap = self.grab()
            
            # Falls grab() fehlschlägt oder leer ist, verwende Screen-Methode
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                # Methode 2: Screenshot vom Screen mit Window-ID
                screen = QApplication.primaryScreen()
                if screen:
                    # Window-ID des Fensters holen
                    win_id = self.winId()
                    if win_id:
                        pixmap = screen.grabWindow(win_id)
            
            # Falls immer noch leer, versuche zentrales Widget zu erfassen
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                central = self.centralWidget()
                if central:
                    pixmap = central.grab()
            
            if pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                QMessageBox.warning(self, "Screenshot", "Fehler beim Erstellen des Screenshots: Leeres Bild.")
                return
            
            # In Zwischenspeicher kopieren - mehrere Methoden versuchen
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
                                ["wl-copy"]  # Fallback falls wl-copy verfügbar ist
                            ]
                        else:
                            # Wayland: wl-copy zuerst
                            commands = [
                                ["wl-copy"],
                                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", temp_path]  # Fallback
                            ]
                        
                        for cmd in commands:
                            try:
                                import subprocess
                                if cmd[0] == "wl-copy":
                                    # wl-copy liest von stdin
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
            
            if not success:
                QMessageBox.warning(
                    self, 
                    "Screenshot", 
                    "Fehler: Bild konnte nicht in den Zwischenspeicher kopiert werden.\n\n"
                    "Mögliche Lösungen:\n"
                    "- wl-copy installieren (Wayland): sudo apt install wl-clipboard\n"
                    "- xclip installieren (X11): sudo apt install xclip"
                )
                return
            
            # Erfolgsmeldung anzeigen
            QMessageBox.information(
                self, 
                "Screenshot", 
                f"Screenshot wurde in den Zwischenspeicher kopiert.\nGröße: {pixmap.width()}×{pixmap.height()} Pixel"
            )
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
    # Qt-Logging für Portal-Fehler unterdrücken (harmlos, aber störend)
    import os
    if "QT_LOGGING_RULES" not in os.environ:
        os.environ["QT_LOGGING_RULES"] = "qt.qpa.services.debug=false"
    
    app = QApplication(sys.argv)
    app.setApplicationName("PI-Installer DSI Radio")
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
    w = DsiRadioWindow()
    w.setWindowTitle(WINDOW_TITLE)  # Bereits in __init__, sicherheitshalber vor show()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
