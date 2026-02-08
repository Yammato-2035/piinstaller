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
from PyQt6.QtCore import Qt, QTimer, QByteArray, QRectF
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush, QColor
from math import pi, cos, sin

BACKEND_BASE = os.environ.get("PI_INSTALLER_BACKEND", "http://127.0.0.1:8000")
METADATA_INTERVAL_MS = 10000
CLOCK_INTERVAL_MS = 1000
WINDOW_TITLE = "PI-Installer DSI Radio"
FAVORITES_MAX = 20
CONFIG_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "pi-installer-dsi-radio",
)
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
                return data
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
        color: #f7fafc; border: 1px solid #4a5568;
        border-radius: 12px; padding: 12px 20px; font-size: 14px;
        min-height: 48px;
        border-bottom: 3px solid #2d3748;
    }
    QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3d4a5c, stop:1 #2d3748); }
    QPushButton:checked { background: #0d9488; color: white; border-bottom-color: #0f766e; }
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
        name = self._search.text().strip()
        def do():
            stations = _fetch_stations_search(name)
            def apply():
                self._list.clear()
                if not stations:
                    for s in RADIO_STATIONS[:50]:
                        item = QListWidgetItem(s.get("name", "") + " – " + ((s.get("stream_url", ""))[:50] + "…" if len(s.get("stream_url", "")) > 50 else s.get("stream_url", "")))
                        item.setData(Qt.ItemDataRole.UserRole, {"name": s.get("name"), "url": s.get("stream_url"), "favicon": s.get("logo_url"), "state": s.get("region"), "tags": s.get("genre")})
                        self._list.addItem(item)
                    if not self._list.count():
                        self._list.addItem(QListWidgetItem("Keine Sender. Backend erreichbar? Senderliste aus Standardliste geladen."))
                    return
                for s in stations:
                    item = QListWidgetItem(s.get("name", "") + " – " + (s.get("url", "")[:50] + "…" if len(s.get("url", "")) > 50 else s.get("url", "")))
                    item.setData(Qt.ItemDataRole.UserRole, s)
                    self._list.addItem(item)
            QTimer.singleShot(0, apply)
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
        main_h = QHBoxLayout(central)
        main_h.setContentsMargins(10, 6, 6, 8)
        main_h.setSpacing(8)
        left = QWidget()
        layout = QVBoxLayout(left)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Radioanzeige: links Logo, rechts schwarzer Klavierlack-Rahmen mit leuchtend grüner Anzeige, Text schwarz
        card = QFrame()
        card.setObjectName("display")
        card.setStyleSheet("background: transparent; border: none;")
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 0)
        # Logo-Platz um 20 % vergrößert (80 → 96)
        self._logo_label = QLabel()
        self._logo_label.setFixedSize(96, 96)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("background-color: transparent; border-radius: 6px; color: #0f172a; font-size: 20px;")
        self._logo_label.setText("…")
        card_layout.addWidget(self._logo_label)
        # Schwarzer Klavierlack-Rahmen, darin leuchtend grüne rechteckige Anzeige (volle Breite)
        black_frame = QFrame()
        black_frame.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #0c0c0c, stop:1 #1a1a1a); border: 1px solid #334155; border-radius: 8px; padding: 6px;")
        black_frame_layout = QHBoxLayout(black_frame)
        black_frame_layout.setContentsMargins(6, 6, 6, 6)
        green_display = QFrame()
        green_display.setStyleSheet("background: #22c55e; border: none; border-radius: 4px; padding: 6px;")
        right = QVBoxLayout(green_display)
        right.setSpacing(2)
        self._station_label = QLabel(self._current_station.get("name", "—"))
        self._station_label.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        self._station_label.setStyleSheet("color: #0f172a; border: none;")
        right.addWidget(self._station_label)
        self._senderinfo_label = QLabel("")
        self._senderinfo_label.setStyleSheet("color: #0f172a; font-size: 12px; border: none;")
        right.addWidget(self._senderinfo_label)
        self._show_label = QLabel("")
        self._show_label.setStyleSheet("color: #0f172a; font-size: 13px; border: none;")
        self._show_label.setWordWrap(True)
        right.addWidget(self._show_label)
        self._now_label = QLabel("Pause")
        self._now_label.setStyleSheet("color: #0f172a; font-size: 14px; border: none;")
        self._now_label.setWordWrap(True)
        right.addWidget(self._now_label)
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #0f172a; font-size: 12px; border: none;")
        right.addWidget(self._info_label)
        black_frame_layout.addWidget(green_display, 1)
        card_layout.addWidget(black_frame, 1)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setToolTip("Schließen")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("font-size: 11px; font-weight: bold; border: none; background: transparent; color: #0f172a; min-width: 20px; max-width: 20px; min-height: 20px; max-height: 20px;")
        card_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        layout.addWidget(card)

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
        # D/A-Schiebeschalter: langgestrecktes rotes O, runder schwarzer Schieber, D (digital) / A (analog)
        vu_switch = QWidget()
        vu_switch_layout = QVBoxLayout(vu_switch)
        vu_switch_layout.setContentsMargins(0, 0, 0, 0)
        da_row = QHBoxLayout()
        da_row.setSpacing(0)
        d_lbl = QLabel("D")
        d_lbl.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: bold; background: transparent;")
        d_lbl.setFixedWidth(14)
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        da_row.addWidget(d_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self._vu_mode_slider = QSlider(Qt.Orientation.Horizontal)
        self._vu_mode_slider.setMinimum(0)
        self._vu_mode_slider.setMaximum(1)
        self._vu_mode_slider.setValue(0)
        self._vu_mode_slider.setFixedWidth(56)
        self._vu_mode_slider.setFixedHeight(28)
        self._vu_mode_slider.setToolTip("D = Digital (LED), A = Analog")
        self._vu_mode_slider.valueChanged.connect(self._on_vu_slider)
        self._vu_mode_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #dc2626;
                height: 20px;
                border-radius: 10px;
            }
            QSlider::handle:horizontal {
                background: #0f172a;
                width: 22px;
                height: 22px;
                margin: -1px 0;
                border-radius: 11px;
            }
            QSlider::sub-page:horizontal { background: #dc2626; border-radius: 10px; }
            QSlider::add-page:horizontal { background: #dc2626; border-radius: 10px; }
        """)
        da_row.addWidget(self._vu_mode_slider, 0, Qt.AlignmentFlag.AlignCenter)
        a_lbl = QLabel("A")
        a_lbl.setStyleSheet("color: #0f172a; font-size: 11px; font-weight: bold; background: transparent;")
        a_lbl.setFixedWidth(14)
        a_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        da_row.addWidget(a_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        vu_switch_layout.addLayout(da_row)
        vu_row.addWidget(vu_switch, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(vu_row)

        # Sender-Buttons + rechts: Lautstärke oberhalb, Umschalter (1/2 ▶) darunter
        self._btn_container = QWidget()
        self._btn_layout = QGridLayout(self._btn_container)
        self._btn_layout.setSpacing(8)
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

        main_h.addWidget(left, 1)

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
                subprocess.run(args, timeout=2, capture_output=True)
                return
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

    def _update_senderinfo(self):
        region = self._current_station.get("region") or ""
        genre = self._current_station.get("genre") or ""
        self._senderinfo_label.setText(" · ".join(x for x in (region, genre) if x))

    def _on_station(self, st: dict):
        was_playing = self._playing
        self._stop_stream()
        self._current_station = st
        for b in self._station_buttons:
            b.setChecked(b.property("station_id") == st.get("id"))
        self._station_label.setText(st.get("name", "—"))
        self._update_senderinfo()
        self._show_label.setText("")
        self._now_label.setText("Pause")
        self._info_label.setText("")
        self._metadata = {}
        self._update_logo()
        self._play_btn.setText("▶ Abspielen")
        self._playing = False
        if was_playing:
            self._start_stream()

    def _update_logo(self):
        url = self._current_station.get("logo_url") or ""
        data = _fetch_logo(url) if url else None
        if data:
            pix = QPixmap()
            pix.loadFromData(QByteArray(data))
            if not pix.isNull():
                self._logo_label.setPixmap(pix.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self._logo_label.setText((self._current_station.get("name") or "?")[:2])
        else:
            self._logo_label.setText((self._current_station.get("name") or "?")[:2])

    def _start_stream(self):
        if not self._player_cmd or self._process:
            return
        url = self._current_station.get("stream_url", "")
        if not url:
            return
        if self._player_cmd == "cvlc":
            cmd = ["cvlc", "--no-video", "--play-and-exit", url]
        elif self._player_cmd == "mpv":
            cmd = ["mpv", "--no-video", "--no-terminal", url]
        else:
            cmd = ["mpg123", "-q", url]
        try:
            self._process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            self._playing = True
            self._play_btn.setText("⏸ Pause")
            self._now_label.setText("Live …")
            self._vu_val_0 = 50
            self._vu_val_1 = 50
            self._metadata_timer.start(METADATA_INTERVAL_MS)
            self._poll_metadata()
            self._vu_timer.start(120)
        except Exception:
            self._playing = False
            self._now_label.setText("Streamfehler")

    def _stop_stream(self):
        self._metadata_timer.stop()
        self._vu_timer.stop()
        for ch in (0, 1, 2):
            self._set_led_strip(ch, 0)
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=3)
            except Exception:
                self._process.kill()
            self._process = None
        self._playing = False

    def _apply_metadata(self, meta: dict):
        if not self._playing:
            return
        self._metadata = meta
        show = (meta.get("show") or meta.get("server_name") or "").strip()
        title = (meta.get("title") or "").strip()
        artist = (meta.get("artist") or "").strip()
        song = (meta.get("song") or "").strip()
        bitrate = meta.get("bitrate")
        if show:
            self._show_label.setText("Sendung: " + show[:60] + ("…" if len(show) > 60 else ""))
        else:
            self._show_label.setText("")
        if artist and song:
            now_text = f"{artist} – {song}"
        elif title:
            now_text = title
        else:
            now_text = "Live"
        self._now_label.setText("Jetzt: " + now_text[:70] + ("…" if len(now_text) > 70 else ""))
        if bitrate:
            self._info_label.setText(f"{bitrate} kbps")
            self._set_led_strip(2, min(100, int(bitrate) if bitrate else 0))
        else:
            self._info_label.setText("")
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
        if not url:
            return
        def do():
            meta = _fetch_metadata(url)
            QTimer.singleShot(0, lambda: self._apply_metadata(meta))
        threading.Thread(target=do, daemon=True).start()

    def _toggle_play(self):
        if self._playing:
            self._stop_stream()
            self._play_btn.setText("▶ Abspielen")
            self._now_label.setText("Pause")
        else:
            self._start_stream()

    def showEvent(self, event):
        """Fenstertitel früh setzen, damit Wayfire-Regel (DSI-1/TFT) greift."""
        self.setWindowTitle(WINDOW_TITLE)
        super().showEvent(event)

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
    app = QApplication(sys.argv)
    app.setApplicationName("PI-Installer DSI Radio")
    # Wayland app_id nur setzen, wenn .desktop-Datei installiert ist – sonst Fehler:
    # "Could not register app ID: App info not found for 'pi-installer-dsi-radio'"
    if hasattr(app, "setDesktopFileName") and _desktop_file_installed():
        app.setDesktopFileName("pi-installer-dsi-radio")
    w = DsiRadioWindow()
    w.setWindowTitle(WINDOW_TITLE)  # Bereits in __init__, sicherheitshalber vor show()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
