#!/usr/bin/env python3
"""
Sabrina Tuner – QML-Prototyp.
UI in QML (qml/main.qml), Logik in Python (GStreamer, Senderliste).
Start: python dsi_radio_qml.py  oder  ./start-dsi-radio-qml.sh
"""

import hashlib
import json
import os
import sys
import signal
import subprocess
import threading
import time
import urllib.parse
import urllib.request

# Projektpfad für Imports
_DSI_RADIO_DIR = os.path.dirname(os.path.abspath(__file__))
if _DSI_RADIO_DIR not in sys.path:
    sys.path.insert(0, _DSI_RADIO_DIR)

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QUrl, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

try:
    from stations import RADIO_STATIONS
except ImportError:
    RADIO_STATIONS = [
        {"id": "einslive", "name": "1Live", "stream_url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3"},
        {"id": "dlf", "name": "Deutschlandfunk", "stream_url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3"},
        {"id": "energy", "name": "Energy", "stream_url": "https://edge62.streamonkey.net/energy-digital/stream/mp3"},
    ]

try:
    import gst_player
except ImportError:
    gst_player = None


def _get_default_audio_sink():
    """PulseAudio/PipeWire Standard-Sink für GStreamer (Tonausgabe)."""
    import subprocess
    for pactl in ("pactl", "/usr/bin/pactl"):
        try:
            env = os.environ.copy()
            env["PATH"] = "/usr/bin:/bin:" + env.get("PATH", "")
            r = subprocess.run(
                [pactl, "get-default-sink"],
                capture_output=True, text=True, timeout=2, env=env
            )
            if r.returncode == 0 and r.stdout and r.stdout.strip():
                return r.stdout.strip()
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            if pactl == "/usr/bin/pactl":
                break
    return None


def _fetch_icy_metadata_direct(url: str, timeout: int = 8) -> dict:
    """Liest einen ICY-Metadaten-Block aus dem Stream (StreamTitle). Läuft in Thread, gleiche Logik wie Backend."""
    try:
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        req = urllib.request.Request(url, headers={"User-Agent": ua, "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            meta_int = resp.headers.get("icy-metaint")
            if not meta_int:
                return {}
            meta_int = int(meta_int)
            resp.read(meta_int)
            raw = resp.read(1)
            if not raw:
                return {}
            block_len = ord(raw) * 16
            if block_len <= 0:
                return {}
            meta_raw = resp.read(block_len).decode("utf-8", errors="ignore").strip("\x00")
            for part in meta_raw.split(";"):
                part = part.strip()
                if part.lower().startswith("streamtitle="):
                    val = part.split("=", 1)[1].strip("'\"").strip("'\"")
                    if val:
                        artist, song = "", val
                        if " - " in val or " – " in val:
                            sep = " - " if " - " in val else " – "
                            parts = val.split(sep, 1)
                            artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                            song = (parts[1].strip() or val) if len(parts) > 1 else val
                        return {"title": val, "artist": artist, "song": song}
    except Exception:
        pass
    return {}


def _get_network_info():
    """Liefert (typ, signal 0.0–1.0): typ = 'wlan' | 'lan'."""
    import subprocess
    try:
        out = subprocess.run(
            ["ip", "-o", "route", "get", "8.8.8.8"],
            capture_output=True, text=True, timeout=1
        )
        if out.returncode != 0 or not out.stdout:
            return "lan", 1.0
        # Zeile enthält "dev <iface>"
        parts = out.stdout.strip().split()
        for i, p in enumerate(parts):
            if p == "dev" and i + 1 < len(parts):
                iface = parts[i + 1]
                break
        else:
            return "lan", 1.0
        if "wlan" in iface or "wl" in iface:
            # Signal aus /proc/net/wireless (Quality, 0–70 typisch)
            try:
                with open("/proc/net/wireless", "r") as f:
                    for line in f:
                        if iface in line.split():
                            parts = line.split()
                            if len(parts) >= 3:
                                qual = int(parts[2].replace(".", ""))  # z.B. 70.
                                return "wlan", min(1.0, qual / 70.0)
            except (OSError, ValueError):
                pass
            return "wlan", 0.5
        return "lan", 1.0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return "lan", 1.0


def _pactl_env():
    """Umgebung für pactl (PulseAudio/PipeWire)."""
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin:" + env.get("PATH", "")
    return env


def _pactl_path():
    """Pactl-Befehl für PulseAudio/PipeWire."""
    for candidate in ("pactl", "/usr/bin/pactl"):
        try:
            if candidate == "pactl":
                r = subprocess.run(["which", "pactl"], capture_output=True, timeout=1, env=_pactl_env())
                if r.returncode == 0:
                    return "pactl"
                continue
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        except Exception:
            continue
    return None


def _get_system_stream_metadata():
    """Liest Titel/Interpret aus PipeWire/Pulse (pactl list sink-inputs).
    Dieselbe Quelle wie der System-Mixer – zeigt also das, was PipeWire anzeigt."""
    out = {}
    pactl = _pactl_path()
    if not pactl:
        return out
    pid_str = str(os.getpid())
    try:
        result = subprocess.run(
            [pactl, "list", "sink-inputs"],
            capture_output=True, text=True, timeout=3, env=_pactl_env(),
        )
        if result.returncode != 0 or not result.stdout:
            return out
        blocks = result.stdout.split("Sink Input #")
        for block in blocks:
            if not block.strip():
                continue
            if f'application.process.id = "{pid_str}"' not in block and f"application.process.id = {pid_str}" not in block:
                continue
            in_props = False
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("Properties:"):
                    in_props = True
                    continue
                if in_props and "=" in line:
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


_BACKEND_BASE = "http://127.0.0.1:8000"

_CONFIG_BASE = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
CONFIG_DIR = os.path.join(_CONFIG_BASE, "pi-installer-dsi-radio")
LAST_STATION_FILE = os.path.join(CONFIG_DIR, "last_station.json")
LOGO_CACHE_DIR = os.path.join(CONFIG_DIR, "logo_cache")
LOGO_CACHE_INDEX = os.path.join(LOGO_CACHE_DIR, "index.json")
LOGO_CACHE_MAX_AGE_DAYS = 14


def _load_last_station():
    """Letzten gespielten Sender laden (wie in dsi_radio.py)."""
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


def _save_last_station(station):
    """Letzten Sender speichern (kompatibel mit dsi_radio.py last_station.json)."""
    url = (station.get("stream_url") or station.get("url") or "").strip()
    if not station or not url:
        return
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        out = {"name": (station.get("name") or "").strip(), "url": url, "stream_url": url}
        if station.get("favicon"):
            out["logo_url"] = (station.get("favicon") or "").strip()
        if station.get("homepage"):
            out["homepage"] = (station.get("homepage") or "").strip()
        if station.get("state"):
            out["region"] = (station.get("state") or "").strip()
        if station.get("tags"):
            out["genre"] = (station.get("tags") or "").strip()
        if station.get("id"):
            out["id"] = station.get("id")
        with open(LAST_STATION_FILE, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _logo_cache_load_index():
    """Logo-Cache-Index laden (URL → path, cached_at)."""
    try:
        if os.path.isfile(LOGO_CACHE_INDEX):
            with open(LOGO_CACHE_INDEX, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def _logo_cache_save_index(index: dict):
    try:
        os.makedirs(LOGO_CACHE_DIR, exist_ok=True)
        with open(LOGO_CACHE_INDEX, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _logo_cache_get(url: str):
    """Liefert file://-Pfad wenn URL gecacht und jünger als LOGO_CACHE_MAX_AGE_DAYS, sonst None."""
    if not (url or "").strip().startswith("http"):
        return None
    index = _logo_cache_load_index()
    entry = index.get(url)
    if not entry or not isinstance(entry, dict):
        return None
    path = entry.get("path")
    cached_at = entry.get("cached_at")
    if not path or not cached_at:
        return None
    full_path = os.path.join(LOGO_CACHE_DIR, path)
    if not os.path.isfile(full_path):
        return None
    try:
        from datetime import datetime, timedelta, timezone
        s = (cached_at or "").replace("Z", "").split("+")[0].strip()
        dt = datetime.fromisoformat(s) if s else None
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - dt > timedelta(days=LOGO_CACHE_MAX_AGE_DAYS):
            return None
    except Exception:
        return None
    return "file://" + os.path.abspath(full_path)


def _logo_cache_download_and_save(url: str, user_agent: str) -> bool:
    """Lädt URL herunter und speichert in Logo-Cache. True bei Erfolg."""
    if not (url or "").strip().startswith("http"):
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
        if not data or len(data) > 5 * 1024 * 1024:
            return False
        ext = ".png"
        if "jpeg" in ctype or "jpg" in ctype:
            ext = ".jpg"
        elif "gif" in ctype:
            ext = ".gif"
        elif "webp" in ctype:
            ext = ".webp"
        key = hashlib.sha256(url.encode()).hexdigest()[:20] + ext
        os.makedirs(LOGO_CACHE_DIR, exist_ok=True)
        full_path = os.path.join(LOGO_CACHE_DIR, key)
        with open(full_path, "wb") as f:
            f.write(data)
        index = _logo_cache_load_index()
        from datetime import datetime, timezone
        index[url] = {"path": key, "cached_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        _logo_cache_save_index(index)
        return True
    except Exception:
        return False


def _normalize_station_name(name: str) -> str:
    """Sendernamen aufräumen: führende Unterstriche, ' by rautemusic' etc."""
    if not name or not isinstance(name, str):
        return (name or "").strip()
    t = name.strip().strip("_")
    for suffix in (" by rautemusic", " by Rautemusic", " by RAUTEMUSIC"):
        if t.endswith(suffix):
            t = t[:-len(suffix)].strip()
    return t or name.strip()


def _station_normalize(s):
    """Einheitliches Dict: name, url, favicon, homepage, country, state, tags, bitrate."""
    url = (s.get("url") or s.get("stream_url") or "").strip()
    raw_name = (s.get("name") or "—").strip()
    name = _normalize_station_name(raw_name) or raw_name
    favicon = (s.get("favicon") or s.get("logo_url") or "").strip() or None
    homepage = (s.get("homepage") or s.get("website") or "").strip() or None
    state = (s.get("state") or s.get("region") or "").strip()
    tags = (s.get("tags") or s.get("genre") or "").strip()
    bitrate = s.get("bitrate")
    if bitrate is not None and not isinstance(bitrate, int):
        try:
            bitrate = int(bitrate)
        except (TypeError, ValueError):
            bitrate = None
    return {
        "name": name,
        "url": url,
        "favicon": favicon,
        "homepage": homepage,
        "country": (s.get("country") or "Germany").strip(),
        "state": state,
        "tags": tags,
        "bitrate": bitrate,
    }


# Ballistik: kürzer für reaktiveres VU (Attack/Release)
_VU_ATTACK_S = 0.15
_VU_RELEASE_S = 0.35
_LEVEL_DT_S = 0.12


class VuMeterBridge(QObject):
    """Bridge für analoge VU-Meter: Pegel in dBFS mit Ballistik, Demo-Modus für UI-Tests."""
    leftDbChanged = pyqtSignal()
    rightDbChanged = pyqtSignal()
    levelsChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._left_db = -80.0
        self._right_db = -80.0
        self._smoothed_left = -80.0
        self._smoothed_right = -80.0
        self._demo_mode = False
        self._demo_phase = 0.0
        self._demo_timer = QTimer(self)
        self._demo_timer.timeout.connect(self._demo_tick)
        self._log_counter = 0  # gedrosseltes Logging

    def get_left_db(self):
        return self._left_db

    def set_left_db(self, val):
        val = max(-80.0, min(0.0, float(val)))
        if abs(self._left_db - val) < 1e-6:
            return
        self._left_db = val
        self.leftDbChanged.emit()
        self.levelsChanged.emit(self._left_db, self._right_db)

    leftDb = pyqtProperty(float, get_left_db, notify=leftDbChanged)

    def get_right_db(self):
        return self._right_db

    def set_right_db(self, val):
        val = max(-80.0, min(0.0, float(val)))
        if abs(self._right_db - val) < 1e-6:
            return
        self._right_db = val
        self.rightDbChanged.emit()
        self.levelsChanged.emit(self._left_db, self._right_db)

    rightDb = pyqtProperty(float, get_right_db, notify=rightDbChanged)

    def get_demo_mode(self):
        return self._demo_mode

    def set_demo_mode(self, on):
        on = bool(on)
        if self._demo_mode == on:
            return
        self._demo_mode = on
        if on:
            self._demo_timer.start(80)
        else:
            self._demo_timer.stop()
        self.demoModeChanged.emit()

    demoModeChanged = pyqtSignal()
    demoMode = pyqtProperty(bool, get_demo_mode, set_demo_mode, notify=demoModeChanged)

    def _smooth_step(self, current: float, target: float, dt: float) -> float:
        """Ein Schritt Ballistik: Attack ~300 ms, Release ~600 ms."""
        tau = _VU_RELEASE_S if target < current else _VU_ATTACK_S
        factor = 1.0 - __import__("math").exp(-dt / tau)
        return max(-80.0, min(0.0, current + (target - current) * factor))

    @pyqtSlot(float, float)
    def update_levels(self, left_db: float, right_db: float):
        """Von RadioBridge aufgerufen (Qt-Hauptthread); wendet Ballistik an und setzt leftDb/rightDb."""
        if self._demo_mode:
            return
        left_db = max(-80.0, min(0.0, float(left_db)))
        right_db = max(-80.0, min(0.0, float(right_db)))
        self._smoothed_left = self._smooth_step(self._smoothed_left, left_db, _LEVEL_DT_S)
        self._smoothed_right = self._smooth_step(self._smoothed_right, right_db, _LEVEL_DT_S)
        self.set_left_db(self._smoothed_left)
        self.set_right_db(self._smoothed_right)

    def _demo_tick(self):
        """Demo-Modus: Sinus-artige Pegel für Rendering-Test."""
        import math
        self._demo_phase += 0.08
        t = self._demo_phase
        # Leicht versetzte L/R, Bereich ca. -35 … -5 dB
        left = -25.0 + 12.0 * math.sin(t)
        right = -25.0 + 12.0 * math.sin(t + 0.7)
        self._smoothed_left = self._smooth_step(self._smoothed_left, left, 0.08)
        self._smoothed_right = self._smooth_step(self._smoothed_right, right, 0.08)
        self.set_left_db(self._smoothed_left)
        self.set_right_db(self._smoothed_right)


class RadioBridge(QObject):
    """Bridge-Objekt für QML: Sender (Backend/Radio-Browser), Favoriten, Lautstärke, Aussteuerung, Netzwerk."""
    currentStationNameChanged = pyqtSignal()
    volumeChanged = pyqtSignal()
    stationCountChanged = pyqtSignal()
    levelChanged = pyqtSignal()
    networkChanged = pyqtSignal()
    backendActiveChanged = pyqtSignal()
    senderlisteFilterChanged = pyqtSignal()
    metadataChanged = pyqtSignal()
    logoFailCountChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stations = []
        self._favorites = []
        self._search_country = "Germany"
        self._search_tag = ""
        self._search_result = []
        self._current_index = -1
        self._current_station_name = ""
        self._metadata_title = ""
        self._metadata_artist = ""
        self._volume = 100
        self._level_left = 0.0
        self._level_right = 0.0
        self._network_type = "lan"
        self._signal_strength = 1.0
        self._backend_active = False
        self._player = None
        self._vu_bridge = VuMeterBridge(self)
        self._logo_failed_urls = set()
        self._logo_fail_count = 0
        if gst_player and gst_player.is_available():
            gst_player.init()
            self._player = gst_player.GstPlayer()
        self.stationCountChanged.emit()
        self._level_timer = QTimer(self)
        self._level_timer.timeout.connect(self._update_level)
        self._level_timer.start(120)
        self._bus_timer = QTimer(self)
        self._bus_timer.timeout.connect(self._poll_gst_bus)
        self._bus_timer.start(150)
        self._network_timer = QTimer(self)
        self._network_timer.timeout.connect(self._update_network)
        self._network_timer.start(2000)
        self._backend_timer = QTimer(self)
        self._backend_timer.timeout.connect(self._update_backend)
        self._backend_timer.start(3000)
        self._metadata_fallback_timer = QTimer(self)
        self._metadata_fallback_timer.timeout.connect(self._poll_metadata_fallback)
        self._metadata_fallback_timer.start(8000)
        self._pulse_metadata_timer = QTimer(self)
        self._pulse_metadata_timer.timeout.connect(self._poll_pulse_metadata)
        self._pulse_metadata_timer.start(2000)
        self._update_network()
        self._update_backend()
        self._load_stations_from_backend_or_fallback()
        QTimer.singleShot(400, self._play_last_station)
        QTimer.singleShot(3500, self._start_logo_cache_fill)

    def _play_last_station(self):
        """Nach Start: letzten gespeicherten Sender abspielen, falls in der Liste."""
        last = _load_last_station()
        if not last:
            return
        url = (last.get("stream_url") or last.get("url") or "").strip()
        if not url:
            return
        for i, s in enumerate(self._stations):
            if ((s.get("url") or s.get("stream_url") or "").strip() == url):
                self.setStation(i)
                return

    def _load_stations_from_backend_or_fallback(self):
        """Favoriten + Suche vom Backend laden, sonst lokale RADIO_STATIONS."""
        self._fetch_favorites()
        self._fetch_search()
        self._merge_stations()
        self.stationCountChanged.emit()

    def _start_logo_cache_fill(self):
        """Startet im Hintergrund das Auffüllen des Logo-Caches (nur wenn nicht gecacht oder älter als 14 Tage)."""
        stations = list(self._stations)
        if not stations:
            return
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        def worker():
            for i in range(len(stations)):
                url = None
                try:
                    favicon = (stations[i].get("favicon") or "").strip()
                    name = (stations[i].get("name") or "").strip()
                    if favicon and (favicon.startswith("http://") or favicon.startswith("https://")):
                        url = favicon
                    elif name and getattr(self, "_backend_active", False):
                        url = f"{_BACKEND_BASE}/api/radio/logo?name=" + urllib.parse.quote(name)
                    if not url:
                        continue
                    if _logo_cache_get(url):
                        continue
                    _logo_cache_download_and_save(url, ua)
                except Exception:
                    pass
                time.sleep(0.6)
        threading.Thread(target=worker, daemon=True).start()

    def _fetch_favorites(self):
        try:
            import urllib.request
            req = urllib.request.Request(f"{_BACKEND_BASE}/api/radio/dsi-config/favorites", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
            favs = (data.get("favorites") or [])
            normalized = [_station_normalize(f) for f in favs if (f.get("stream_url") or f.get("url") or "").strip()]
            # Keine doppelten Einträge (nach URL)
            seen = set()
            self._favorites = []
            for s in normalized:
                u = (s.get("url") or "").strip()
                if u and u not in seen:
                    seen.add(u)
                    self._favorites.append(s)
        except Exception:
            self._favorites = []

    def _fetch_search(self):
        try:
            import urllib.request
            import urllib.parse
            params = urllib.parse.urlencode({"country": self._search_country, "limit": 300, **({"tag": self._search_tag} if self._search_tag else {})})
            req = urllib.request.Request(f"{_BACKEND_BASE}/api/radio/stations/search?{params}", headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            raw = (data.get("stations") or [])
            normalized = [_station_normalize(s) for s in raw if (s.get("url") or "").strip()]
            seen_urls = set()
            self._search_result = []
            for s in normalized:
                u = (s.get("url") or "").strip()
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    self._search_result.append(s)
        except Exception:
            self._search_result = []
        if not self._search_result and not self._favorites:
            self._search_result = [_station_normalize(s) for s in list(RADIO_STATIONS)[:64]]

    def _merge_stations(self):
        """Favoriten zuerst, dann Suchresultat (ohne Duplikate nach URL).
        Bekannte Sender (radioeins, rbb 88.8, Energy) bekommen unsere getestete URL+Favicon,
        damit im QML-Player Ton läuft (API-URLs sind oft tokenisiert/anderer Host)."""
        def norm(u):
            return (u or "").strip()
        # Name → (url, favicon) aus RADIO_STATIONS für URL/Favicon-Override (Ton + Logo)
        def name_key(n):
            k = (n or "").strip().lower().replace(" 88,8", " 88.8")
            return k
        known_by_name = {}
        for ref in list(RADIO_STATIONS):
            n = (ref.get("name") or "").strip()
            if n:
                key = name_key(n)
                val = (norm(ref.get("stream_url") or ref.get("url")), (ref.get("logo_url") or "").strip() or None)
                known_by_name[key] = val
                if " 88.8" in key:
                    known_by_name[key.replace(" 88.8", " 88,8")] = val
        seen_urls = set()
        out = []
        for s in self._favorites:
            u = norm(s.get("url"))
            if u and u not in seen_urls:
                seen_urls.add(u)
                out.append(dict(s))
        for s in self._search_result:
            u = norm(s.get("url"))
            if u and u not in seen_urls:
                seen_urls.add(u)
                out.append(dict(s))
        # Override: bekannte Sender mit unserer URL/Favicon (Ton + Logo)
        for st in out:
            key = name_key(st.get("name") or "")
            if key and key in known_by_name:
                k_url, k_favicon = known_by_name[key]
                if k_url:
                    st["url"] = k_url
                if k_favicon:
                    st["favicon"] = k_favicon
        self._stations = out[:64]
        # Favoriten-URLs an _stations angleichen (nach Override), damit Senderliste/Buttons übereinstimmen
        for f in self._favorites:
            fu = norm(f.get("url"))
            fn = (f.get("name") or "").strip()
            for st in self._stations:
                if norm(st.get("url")) == fu:
                    f["url"] = st.get("url") or f.get("url")
                    break
            else:
                if fn:
                    for st in self._stations:
                        if (st.get("name") or "").strip() == fn:
                            f["url"] = st.get("url") or f.get("url")
                            break

    def _save_favorites(self):
        try:
            import urllib.request
            body = json.dumps({"favorites": [
                {"name": s["name"], "stream_url": s["url"], "logo_url": s.get("favicon") or "", "homepage": s.get("homepage") or "", "region": s.get("state") or "", "genre": s.get("tags") or ""}
                for s in self._favorites[:64]
            ]}).encode("utf-8")
            req = urllib.request.Request(f"{_BACKEND_BASE}/api/radio/dsi-config/favorites", data=body, method="PUT", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3):
                pass
        except Exception:
            pass

    def _poll_gst_bus(self):
        """GStreamer-Bus verarbeiten (TAG → Metadaten im Display, Level)."""
        if self._player and hasattr(self._player, "poll_bus"):
            try:
                self._player.poll_bus()
            except Exception:
                pass

    def _update_level(self):
        import random
        # Echte Pegel für LED-Anzeige (0..1) und für analoges VU (dB)
        if self._player and self._current_index >= 0:
            peaks = self._player.get_peak_levels()
            if peaks is not None:
                self._level_left, self._level_right = peaks[0] / 100.0, peaks[1] / 100.0
            else:
                self._level_left = min(1.0, max(0.0, self._level_left * 0.7 + random.uniform(0.05, 0.35)))
                self._level_right = min(1.0, max(0.0, self._level_right * 0.7 + random.uniform(0.05, 0.35)))
            db = self._player.get_peak_levels_db() if hasattr(self._player, "get_peak_levels_db") else None
            if db is not None and self._vu_bridge and not self._vu_bridge.demoMode:
                import math
                vol = max(0.01, self._volume / 100.0)
                adj_db = 20.0 * math.log10(vol)
                self._vu_bridge.update_levels(db[0] + adj_db, db[1] + adj_db)
        else:
            self._level_left = 0.0
            self._level_right = 0.0
            # Bei Stille: VU-Bridge langsam auf -80 zurück (über update_levels mit -80)
            if self._vu_bridge and not self._vu_bridge.demoMode:
                self._vu_bridge.update_levels(-80.0, -80.0)
        self.levelChanged.emit()

    def _update_network(self):
        typ, strength = _get_network_info()
        if typ != self._network_type or abs(strength - self._signal_strength) > 0.05:
            self._network_type = typ
            self._signal_strength = strength
            self.networkChanged.emit()

    def _on_stream_tag(self, meta):
        """Von poll_bus (bereits Qt-Hauptthread) aufgerufen; Metadaten sofort anwenden."""
        if meta:
            self._apply_metadata(dict(meta))

    def _apply_metadata(self, meta):
        """Metadaten (title/artist) aus GStreamer-Tag-Dict extrahieren – dieselbe Quelle wie PipeWire (media.title/artist)."""
        if not meta or not isinstance(meta, dict):
            return
        m = {}
        for k, v in meta.items():
            if not k:
                continue
            s = (v if isinstance(v, str) else str(v) if v is not None else "").strip()
            if s:
                m[k.lower()] = s
        def get_(*keys):
            for k in keys:
                if k and m.get(k, "").strip():
                    return m.get(k, "").strip()
            return ""

        title = get_("title", "stream-title", "streamtitle", "icy-title") or ""
        artist = get_("artist", "album-artist", "album_artist") or ""
        song = get_("song") or ""
        if not title:
            for v in m.values():
                if v and (" - " in v or " – " in v or " \u2013 " in v):
                    title = v
                    break

        if title and not (artist or song) and (" - " in title or " – " in title or " \u2013 " in title):
            for sep in (" – ", " \u2013 ", " - "):
                if sep in title:
                    parts = title.split(sep, 1)
                    artist = (parts[0].strip() or "") if len(parts) > 0 else ""
                    title = (parts[1].strip() or title) if len(parts) > 1 else title
                    break
        if not title and (artist or song):
            title = f"{artist} - {song}".strip() if (artist and song) else (artist or song)

        title = str(title).strip()
        artist = str(artist).strip()
        self._metadata_title = title
        self._metadata_artist = artist
        if title or artist:
            self.metadataChanged.emit()

    def _apply_metadata_from_fallback(self, meta: dict):
        """Metadaten aus Backend/ICY-Fallback anwenden (Hauptthread, z. B. aus Timer/Thread)."""
        if meta and isinstance(meta, dict):
            self._apply_metadata(meta)

    def _poll_pulse_metadata(self):
        """Alle 2 s: Titel/Interpret aus PipeWire lesen (pactl) – dieselbe Quelle wie der System-Mixer.
        So werden Metadaten angezeigt, sobald PipeWire sie hat (auch wenn GStreamer TAG nicht ankommt)."""
        if not self._player or not self._player.is_active or self._current_index < 0:
            return
        def worker():
            meta = _get_system_stream_metadata()
            if meta and (meta.get("title") or meta.get("artist")):
                QTimer.singleShot(0, lambda: self._apply_metadata(meta))
        threading.Thread(target=worker, daemon=True).start()

    def _poll_metadata_fallback(self):
        """Alle 8 s: Wenn Stream läuft, Metadaten per Backend oder direkte ICY-Abfrage holen.
        playbin liefert bei vielen Streams keine TAG-Events (kein icydemux) → Fallback nötig."""
        if not self._player or not self._player.is_active:
            return
        if self._current_index < 0 or self._current_index >= len(self._stations):
            return
        station = self._stations[self._current_index]
        url = (station.get("stream_url") or station.get("url") or "").strip()
        if not url:
            return
        # 1) Backend versuchen (kurzer Timeout, nicht blockieren)
        try:
            meta_url = f"{_BACKEND_BASE}/api/radio/stream-metadata?url={urllib.parse.quote(url, safe='')}"
            req = urllib.request.Request(meta_url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, dict) and (data.get("title") or data.get("artist") or data.get("song")):
                    meta = {"title": (data.get("title") or "").strip(), "artist": (data.get("artist") or "").strip(), "song": (data.get("song") or "").strip()}
                    if meta.get("title") or meta.get("artist"):
                        self._apply_metadata_from_fallback(meta)
                    return
        except Exception:
            pass
        # 2) ICY direkt in Thread, Ergebnis im Hauptthread anwenden
        def worker():
            result = _fetch_icy_metadata_direct(url)
            if result:
                QTimer.singleShot(0, lambda: self._apply_metadata_from_fallback(result))
        threading.Thread(target=worker, daemon=True).start()

    def _update_backend(self):
        active = False
        try:
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:8000/health", method="GET")
            with urllib.request.urlopen(req, timeout=1) as _:
                active = True
        except Exception:
            pass
        if active != self._backend_active:
            self._backend_active = active
            self.backendActiveChanged.emit()

    @pyqtProperty(int, notify=logoFailCountChanged)
    def logoFailCount(self):
        return self._logo_fail_count

    @pyqtProperty(bool, notify=backendActiveChanged)
    def backendActive(self):
        return self._backend_active

    @pyqtProperty(float, notify=levelChanged)
    def levelLeft(self):
        return self._level_left

    @pyqtProperty(float, notify=levelChanged)
    def levelRight(self):
        return self._level_right

    @pyqtProperty(str, notify=networkChanged)
    def networkType(self):
        return self._network_type

    @pyqtProperty(float, notify=networkChanged)
    def signalStrength(self):
        return self._signal_strength

    @pyqtProperty(float, notify=levelChanged)
    def level(self):
        return max(self._level_left, self._level_right)

    @pyqtProperty(int, notify=volumeChanged)
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        v = max(0, min(100, int(value)))
        if v != self._volume:
            self._volume = v
            self.volumeChanged.emit()
            if self._player:
                self._player.set_volume(v / 100.0)

    @pyqtProperty(str, notify=currentStationNameChanged)
    def currentStationName(self):
        return self._current_station_name

    @pyqtProperty(int, notify=currentStationNameChanged)
    def currentStationIndex(self):
        return self._current_index

    @pyqtProperty(str, notify=metadataChanged)
    def currentMetadataTitle(self):
        return self._metadata_title

    @pyqtProperty(str, notify=metadataChanged)
    def currentMetadataArtist(self):
        return self._metadata_artist

    @pyqtProperty(int, notify=stationCountChanged)
    def stationCount(self):
        return len(self._stations)

    @pyqtSlot(int)
    def setVolume(self, value):
        self.volume = value

    def _do_play_station(self, station: dict, url: str):
        """Verzögert ausgeführt: Player starten, damit UI sofort reagiert."""
        _save_last_station(station)
        if not self._player:
            return
        try:
            self._player.set_callbacks(on_tag=self._on_stream_tag)
            audio_sink = _get_default_audio_sink()
            self._player.set_uri(url, pulse_sink_name=audio_sink)
            self._player.play()
            self._player.set_volume(self._volume / 100.0)
            # Metadaten früh und mehrfach: GStreamer TAG fehlt oft, PipeWire/Backend/ICY nutzen
            QTimer.singleShot(150, self._poll_metadata_fallback)
            QTimer.singleShot(300, self._poll_pulse_metadata)
            QTimer.singleShot(500, self._poll_metadata_fallback)
            QTimer.singleShot(1000, self._poll_pulse_metadata)
            QTimer.singleShot(1200, self._poll_metadata_fallback)
            QTimer.singleShot(2500, self._poll_metadata_fallback)
        except Exception:
            pass

    @pyqtSlot(int)
    def setStation(self, index):
        if index < 0 or index >= len(self._stations):
            return
        station = self._stations[index]
        url = (station.get("stream_url") or station.get("url") or "").strip()
        name = (station.get("name") or "—").strip()
        if not url:
            return
        self._current_index = index
        self._current_station_name = name
        self._metadata_title = ""
        self._metadata_artist = ""
        self.metadataChanged.emit()
        self.currentStationNameChanged.emit()
        # Play im nächsten Event-Loop-Tick, damit UI sofort umschaltet
        QTimer.singleShot(0, lambda: self._do_play_station(station, url))

    @pyqtSlot(int, result=str)
    def stationName(self, index):
        if 0 <= index < len(self._stations):
            return (self._stations[index].get("name") or "").strip()
        return ""

    @pyqtSlot(str, str)
    def setSearchFilter(self, country, tag):
        self._search_country = (country or "Germany").strip() or "Germany"
        self._search_tag = (tag or "").strip()
        self._fetch_search()
        self._merge_stations()
        self.stationCountChanged.emit()
        self.senderlisteFilterChanged.emit()

    @pyqtProperty(str, notify=senderlisteFilterChanged)
    def searchCountry(self):
        return self._search_country

    @pyqtProperty(str, notify=senderlisteFilterChanged)
    def searchTag(self):
        return self._search_tag

    def _norm_url(self, u):
        """URL für Favoriten-Vergleich normalisieren (Strip, trailing slash)."""
        return (u or "").strip().rstrip("/")

    @pyqtSlot(int)
    def toggleFavorite(self, index):
        if index < 0 or index >= len(self._stations):
            return
        s = self._stations[index]
        url = self._norm_url(s.get("url"))
        fav_urls = {self._norm_url(f.get("url")) for f in self._favorites}
        if url and url in fav_urls:
            self._favorites = [f for f in self._favorites if self._norm_url(f.get("url")) != url]
        else:
            if url and url not in fav_urls:
                self._favorites.insert(0, dict(s))
        self._save_favorites()
        self._merge_stations()
        self.stationCountChanged.emit()

    @pyqtSlot(int, result=bool)
    def isFavorite(self, index):
        if index < 0 or index >= len(self._stations):
            return False
        url = self._norm_url(self._stations[index].get("url"))
        if not url:
            return False
        return any(self._norm_url(f.get("url")) == url for f in self._favorites)

    @pyqtSlot(str)
    def reportLogoFailed(self, url: str):
        """QML: Image-Status Error (429/404). Nur in dieser Session nicht erneut laden – beim nächsten Start erneut versuchen (wie Shortwave/radio-browser.info)."""
        u = (url or "").strip()
        if not u or u in self._logo_failed_urls:
            return
        self._logo_failed_urls.add(u)
        self._logo_fail_count += 1
        self.logoFailCountChanged.emit()

    def _get_station_logo_url_raw(self, index):
        """Liefert die Logo-URL für einen Sender (ohne Cache)."""
        if index < 0 or index >= len(self._stations):
            return ""
        favicon = (self._stations[index].get("favicon") or "").strip()
        name = (self._stations[index].get("name") or "").strip()
        if not favicon and not name:
            return ""
        if favicon and (favicon.startswith("http://") or favicon.startswith("https://")):
            return favicon
        if self._backend_active and name:
            return f"{_BACKEND_BASE}/api/radio/logo?name=" + urllib.parse.quote(name)
        return ""

    @pyqtSlot(int, result=str)
    def getStationLogoUrl(self, index):
        if index < 0 or index >= len(self._stations):
            return ""
        url = self._get_station_logo_url_raw(index)
        if not url:
            return ""
        if url in self._logo_failed_urls:
            return ""
        cached = _logo_cache_get(url)
        if cached:
            return cached
        return url

    @pyqtSlot(int, result=str)
    def getStationCountry(self, index):
        if 0 <= index < len(self._stations):
            return (self._stations[index].get("country") or "").strip()
        return ""

    @pyqtSlot(int, result=str)
    def getStationGenre(self, index):
        if 0 <= index < len(self._stations):
            return (self._stations[index].get("tags") or "").strip()
        return ""

    @pyqtSlot(int, result=str)
    def getStationQuality(self, index):
        """Sendungsqualität für Tooltip, z. B. '128 kbps MP3' oder '—'."""
        if index < 0 or index >= len(self._stations):
            return "—"
        s = self._stations[index]
        br = s.get("bitrate")
        if br is not None and isinstance(br, int) and br > 0:
            return f"{br} kbps MP3"
        # Aus URL schätzen (z. B. …/128/mp3/…)
        url = (s.get("url") or "").strip()
        if url and "/128/" in url:
            return "128 kbps MP3"
        if url and "/256/" in url:
            return "256 kbps MP3"
        if url and "/320/" in url:
            return "320 kbps MP3"
        if url and "/64/" in url:
            return "64 kbps MP3"
        return "MP3"

    @pyqtSlot()
    def quit(self):
        if self._player:
            try:
                self._player.stop()
            except Exception:
                pass
        app = QGuiApplication.instance()
        if app:
            app.quit()


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Sabrina Tuner (QML)")
    app.setQuitOnLastWindowClosed(True)
    # Ctrl+C im Terminal beendet die App sauber
    def sigint_quit(*_args):
        QTimer.singleShot(0, app.quit)
    try:
        signal.signal(signal.SIGINT, sigint_quit)
    except (ValueError, OSError):
        pass
    engine = QQmlApplicationEngine()
    qml_dir = os.path.join(_DSI_RADIO_DIR, "qml")
    engine.setBaseUrl(QUrl.fromLocalFile(qml_dir))
    icon_path = os.path.join(qml_dir, "sabrina-tuner-icon.png")
    engine.rootContext().setContextProperty("sabrinaTunerIconPath", "file://" + icon_path)
    bridge = RadioBridge()
    engine.rootContext().setContextProperty("radio", bridge)
    engine.rootContext().setContextProperty("vuBridge", bridge._vu_bridge)
    qml_file = os.path.join(qml_dir, "main.qml")
    if not os.path.isfile(qml_file):
        print("Fehler: main.qml nicht gefunden:", qml_file, file=sys.stderr)
        return 1
    engine.load(QUrl.fromLocalFile(qml_file))
    if not engine.rootObjects():
        print("Fehler: QML konnte nicht geladen werden.", file=sys.stderr)
        return 1
    print("Sabrina Tuner (QML): Fenster geöffnet. Beenden: Fenster schließen (X), Ausschalter (⏻) oder Strg+C im Terminal.", flush=True)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
