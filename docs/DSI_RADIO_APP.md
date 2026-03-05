# PI-Installer DSI Radio (Standalone-App)

Eigener Bereich für die **Radio-App** des PI-Installers: die DSI-Radio-Standalone-Anwendung für das Freenove 4,3" DSI-Display.

---

## Übersicht

- **Name:** PI-Installer DSI Radio  
- **Version:** 2.0 (ab Version 2.0: GStreamer-Wiedergabe)  
- **Zweck:** Internetradio auf dem DSI-TFT (Freenove) mit Favoriten, Senderliste und Klavierlack-Design.  
- **Technik:** PyQt6, GStreamer (playbin), PulseAudio/PipeWire. Kein VLC/mpv mehr nötig.

---

## Versionen

| Version | Wiedergabe        | Anmerkung                          |
|--------|-------------------|------------------------------------|
| 1.x    | VLC / mpv / mpg123| Externe Player als Subprocess      |
| **2.0**| **GStreamer**     | In-Process, weniger Ressourcen     |

Die **Radio-App** hat eine eigene Versionsnummer (z. B. 2.0.0), unabhängig von der PI-Installer-Hauptversion.

---

## Voraussetzungen

- **Python:** 3.9+  
- **PyQt6**  
- **GStreamer 1.0** und Python-Bindings:
  - Debian / Raspberry Pi OS:  
    `python3-gi`, `gstreamer1.0-tools`, `gstreamer1.0-plugins-good`, `gstreamer1.0-plugins-bad`, `gstreamer1.0-pulseaudio`
- Optional: Backend (PI-Installer) für Metadaten-Abruf und Radio-Browser-API.

---

## Start

- **Skript:** `./scripts/start-dsi-radio.sh`  
- **Direkt:** `python3 apps/dsi_radio/dsi_radio.py` (aus Projektroot)  
- **Wayfire:** Fenstertitel „PI-Installer DSI Radio“ → Regel für `start_on_output` DSI-1.

---

## Funktionen (u. a.)

- 20 Favoriten-Slots, paginiert  
- Senderliste aus Radio-Browser-API (Backend)  
- Klavierlack- und Wechseldesigns (Theme)  
- Lautstärke, VU-Anzeige (LED/analog)  
- Metadaten (Titel/Interpret) wie bei Shortwave aus dem Stream: GStreamer-Tags (ICY/Stream-Title) und Backend (Icecast/ICY-Fallback)
- Sender von radio-browser.info über Backend-Suche nutzbar; Logos der Sender werden mitgeliefert
- Beim Start: Prüfung der Favoriten-Streams im Hintergrund; nicht erreichbare Sender werden rot mit „kein Stream“ markiert
- Ausgabe über Standard-PulseAudio-Sink (Freenove: HDMI, Mediaboard routet an Gehäuselautsprecher)

---

## Konfiguration

- **Verzeichnis:** `~/.config/pi-installer-dsi-radio/`  
- **Dateien:** `favorites.json`, `theme.txt`, ggf. `stream_error.log`, `audio_sink.log`, `startup_error.log` (bei Absturz)

**Absturz:** Wenn die App sofort abstürzt, erscheint ein Fehlerdialog mit Hinweis auf das Log. Details: `~/.config/pi-installer-dsi-radio/startup_error.log`. Beim Start aus der Konsole wird der Fehler auch dort ausgegeben.

---

## Doku im Projekt

- **Installation / Skripte:** `scripts/install-dsi-radio-on-pi.sh`, `scripts/start-dsi-radio.sh`  
- **Freenove Audio:** `docs/FREENOVE_AUDIO_*.md`  
- **In-App-Dokumentation:** Seite „Dokumentation“ → Abschnitt **Radio-App**.
