# PI-Installer DSI Radio – GStreamer-Player (ab Version 2.0)
# In-Process-Wiedergabe statt VLC/mpv-Subprocess. Nutzt playbin → PulseAudio/ALSA.

from typing import Optional, Callable, Any
import threading

_GST_AVAILABLE = False
_Gst = None
_GST_IMPORT_ERROR: Optional[str] = None

try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst, GObject
    _Gst = Gst
    _GObject = GObject
    _GST_AVAILABLE = True
except (ImportError, ValueError) as e:
    _GST_IMPORT_ERROR = str(e).strip() or type(e).__name__
    _GObject = None


def is_available() -> bool:
    return _GST_AVAILABLE


def get_availability_error() -> Optional[str]:
    """Gibt die Fehlermeldung zurück, falls GStreamer nicht verfügbar ist."""
    return _GST_IMPORT_ERROR


def init() -> bool:
    """GStreamer initialisieren. Muss einmal vor Nutzung aufgerufen werden."""
    if not _GST_AVAILABLE or _Gst is None:
        return False
    try:
        _Gst.init(None)
    except Exception:
        return False
    return True


def _db_to_linear_0_100(db: float) -> int:
    """Peak in dB (-60 … 0) auf Anzeige 0–100 abbilden."""
    if db <= -60:
        return 0
    if db >= 0:
        return 100
    return int(round((db + 60) / 60 * 100))


class GstPlayer:
    """Einfacher GStreamer-Playbin für Internetradio-Streams."""

    def __init__(self):
        self._playbin: Any = None
        self._bus: Any = None
        self._level: Any = None
        self._peak_l: float = -60.0
        self._peak_r: float = -60.0
        self._on_error: Optional[Callable[[str], None]] = None
        self._on_tag: Optional[Callable[[dict], None]] = None

    def set_uri(self, url: str, pulse_sink_name: Optional[str] = None) -> None:
        if not _GST_AVAILABLE or _Gst is None:
            return
        self.stop()
        self._playbin = _Gst.ElementFactory.make("playbin", "player")
        if not self._playbin:
            self._playbin = _Gst.ElementFactory.make("playbin3", "player")
        if not self._playbin:
            raise RuntimeError("GStreamer playbin/playbin3 nicht verfügbar")
        self._playbin.set_property("uri", url)
        self._playbin.set_property("volume", 1.0)
        # Level-Element für echte VU-Pegel (L/R) als Audio-Filter
        self._level = _Gst.ElementFactory.make("level", "level")
        if self._level:
            self._level.set_property("message", True)
            self._level.set_property("interval", 50 * 10**6)  # 50 ms
            self._playbin.set_property("audio-filter", self._level)
        else:
            self._level = None
        self._peak_l = -60.0
        self._peak_r = -60.0
        # Expliziten PulseAudio-Sink setzen, damit Ausgabe auf dem gewählten Gerät landet (z. B. Gehäuse-Lautsprecher)
        if pulse_sink_name and pulse_sink_name.strip():
            sink = _Gst.ElementFactory.make("pulsesink", "audiosink")
            if sink:
                sink.set_property("device", pulse_sink_name.strip())
                self._playbin.set_property("audio-sink", sink)
        self._bus = self._playbin.get_bus()
        self._bus.add_signal_watch()

    def play(self) -> None:
        if self._playbin is None:
            return
        self._playbin.set_state(_Gst.State.PLAYING)

    def stop(self) -> None:
        if self._playbin is None:
            return
        self._playbin.set_state(_Gst.State.NULL)
        self._playbin = None
        self._bus = None
        self._level = None
        self._peak_l = -60.0
        self._peak_r = -60.0

    def set_volume(self, linear: float) -> None:
        """linear: 0.0 .. 2.0 (1.0 = 100%)."""
        if self._playbin is not None:
            self._playbin.set_property("volume", max(0.0, min(2.0, linear)))

    def _parse_level_message(self, msg: Any) -> None:
        """Level-Element-Nachricht auswerten und Peak L/R speichern."""
        if not msg or self._level is None or msg.src != self._level:
            return
        struct = msg.get_structure()
        if not struct or struct.get_name() != "level":
            return
        try:
            peak_val = struct.get_value("peak")
            n = _Gst.ValueList.get_size(peak_val)
            if n >= 1:
                v0 = _Gst.ValueList.get_value(peak_val, 0)
                self._peak_l = v0.get_double() if hasattr(v0, "get_double") else float(v0)
            if n >= 2:
                v1 = _Gst.ValueList.get_value(peak_val, 1)
                self._peak_r = v1.get_double() if hasattr(v1, "get_double") else float(v1)
            else:
                self._peak_r = self._peak_l  # Mono: gleicher Pegel für R
        except Exception:
            pass

    def get_peak_levels(self) -> Optional[tuple]:
        """Letzte Peak-Pegel L/R (0–100). None wenn keine Level-Daten."""
        if self._level is None:
            return None
        return (_db_to_linear_0_100(self._peak_l), _db_to_linear_0_100(self._peak_r))

    def poll_bus(self) -> bool:
        """Bus-Nachrichten verarbeiten. Von Haupt-Thread (z. B. QTimer) aufrufen.
        Gibt True zurück wenn noch aktiv, False bei EOS/ERROR."""
        if self._bus is None:
            return True
        types = _Gst.MessageType.EOS | _Gst.MessageType.ERROR | _Gst.MessageType.TAG | _Gst.MessageType.ELEMENT
        while True:
            msg = self._bus.pop_filtered(types)
            if msg is None:
                break
            if msg.type == _Gst.MessageType.ELEMENT:
                self._parse_level_message(msg)
                continue
            if msg.type == _Gst.MessageType.EOS:
                self.stop()
                return False
            if msg.type == _Gst.MessageType.ERROR:
                err, _ = msg.parse_error()
                err_str = err.message if err else "Unbekannter Fehler"
                if self._on_error:
                    self._on_error(err_str)
                self.stop()
                return False
            if msg.type == _Gst.MessageType.TAG:
                taglist = msg.parse_tag()
                if taglist and self._on_tag:
                    meta = {}

                    def _add_tag(tag_list: Any, tag: str, *_: Any) -> None:
                        try:
                            v = tag_list.get_value(tag)
                            if v is None:
                                meta[tag] = ""
                                return
                            if _GObject is not None and v.type == _GObject.TYPE_STRING:
                                val = v.get_string()
                                meta[tag] = (val or "").strip()
                            else:
                                # Nicht-String (z. B. erstes Feld einer Structure) als String versuchen
                                try:
                                    s = str(v)
                                    if s and s != str(type(v)):
                                        meta[tag] = s.strip()
                                    else:
                                        meta[tag] = ""
                                except Exception:
                                    meta[tag] = ""
                        except Exception:
                            meta[tag] = ""

                    taglist.foreach(_add_tag)
                    # Normalisierung: ICY/Stream liefern oft stream-title statt title (z. B. Radio SAW/streamABC)
                    if meta:
                        if not (meta.get("title") or "").strip():
                            for key in ("stream-title", "streamtitle", "icy-title"):
                                val = (meta.get(key) or "").strip()
                                if val:
                                    meta["title"] = val
                                    break
                        if not (meta.get("title") or "").strip():
                            # Fallback: beliebiger Tag mit "Artist - Titel"-Format (wie Lautstärkeregler bei SAW)
                            for key, val in meta.items():
                                v = (val or "").strip()
                                if v and (" - " in v or " – " in v or "\u2013" in v):
                                    meta["title"] = v
                                    break
                        if (meta.get("organization") or "").strip() and not (meta.get("show") or "").strip():
                            meta["show"] = (meta.get("organization") or "").strip()
                    if meta:
                        self._set_pulse_stream_properties(meta)
                        self._on_tag(meta)
        return self._playbin is not None

    def _set_pulse_stream_properties(self, meta: dict) -> None:
        """Setzt PulseAudio/PipeWire Stream-Properties (media.title, media.artist) am Sink.
        So sieht der Lautstärkeregler dieselben Metadaten wie die App."""
        if not _GST_AVAILABLE or _Gst is None or not self._playbin:
            return
        try:
            sink = self._playbin.get_property("audio-sink")
            if sink is None:
                return
            factory = sink.get_factory()
            if not factory or factory.get_name() != "pulsesink":
                return
            title = (meta.get("title") or "").strip()
            artist = (meta.get("artist") or "").strip()
            if not title and not artist:
                return
            parts = ["props"]
            if title:
                safe = title.replace("\\", "\\\\").replace(",", "\\,")
                parts.append(f"media.title={safe}")
            if artist:
                safe = artist.replace("\\", "\\\\").replace(",", "\\,")
                parts.append(f"media.artist={safe}")
            if len(parts) <= 1:
                return
            struct_str = ",".join(parts)
            st = _Gst.Structure.from_string(struct_str)
            if st:
                sink.set_property("stream-properties", st)
        except Exception:
            pass

    def set_callbacks(self, on_error: Optional[Callable[[str], None]] = None, on_tag: Optional[Callable[[dict], None]] = None) -> None:
        self._on_error = on_error
        self._on_tag = on_tag

    @property
    def is_active(self) -> bool:
        return self._playbin is not None
