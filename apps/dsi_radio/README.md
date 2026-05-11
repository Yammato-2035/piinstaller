# DSI-Radio – eigenständige PyQt6-App

**Version 2.1.0** (Stand: PI-Installer 1.3.4.2)

Das Radio läuft als **eigene PyQt-App** (kein Webbrowser, kein PI-Installer-Frontend nötig). Geeignet für das Freenove 4,3″ DSI-Display; das Fenster wird per Wayfire-Regel auf DSI-1 gelegt. Ab 2.1: NDR 1/NDR 2 nutzen bevorzugt getestete icecast-URLs (Ton und Metadaten).

## Start

- Aus dem Projektroot: `./scripts/start-dsi-radio-native.sh`
- Oder: `./scripts/start-dsi-radio.sh` (startet dieselbe PyQt-App, mit Browser-Fallback nur wenn PyQt6 fehlt)
- Desktop-Verknüpfung „DSI Radio“ startet die PyQt-App direkt.

## Voraussetzungen

- Python 3 mit PyQt6 (siehe `requirements.txt`)
- **Backend (Port 8000):** Für Sendersuche, Metadaten (Now Playing) und Logo-Proxy muss das PI-Installer-Backend laufen (z. B. als Service `pi-installer.service` oder manuell `./start-backend.sh` im Projektroot). Ohne Backend: Radio-Streams und eingebaute Senderliste funktionieren, Logos und Sendersuche können fehlen.

```bash
cd apps/dsi_radio
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Abhängigkeiten

- **PyQt6** – Oberfläche (per pip in der Venv)
- **GStreamer + Python-Bindings (gi)** – Audiowiedergabe (Systempakete)

Falls beim Senderstart „GStreamer nicht verfügbar – No module named 'gi'“ erscheint, oder ein Sender (z. B. NDR 1) Metadaten zeigt aber keinen Ton:

**Im Terminal auf dem Linux-Rechner:**

1. Terminal öffnen.
2. In das Projektverzeichnis wechseln (dort, wo sich der Ordner `scripts/` befindet), z. B.:
   ```bash
   cd ~/piinstaller
   ```
   bzw. dorthin, wo das Repo bei Ihnen liegt (z. B. `/home/volker/piinstaller`).
3. Setup-Skript **mit `bash`** ausführen (funktioniert auch bei falschen Zeilenumbrüchen):
   ```bash
   sudo bash ./scripts/install-dsi-radio-setup.sh
   ```
   Oder mit **vollem Pfad** (an Ihren Benutzer und Pfad anpassen):
   ```bash
   sudo bash /home/volker/piinstaller/scripts/install-dsi-radio-setup.sh
   ```
4. DSI Radio **komplett beenden** und wieder starten (Desktop-Starter oder `./scripts/start-dsi-radio.sh`).

**„Befehl nicht gefunden“** beim Aufruf von `sudo /pfad/.../install-dsi-radio-setup.sh`:
- Stattdessen **`sudo bash /pfad/.../install-dsi-radio-setup.sh`** verwenden (mit `bash`).
- Prüfen, ob die Datei existiert: `ls -la /home/volker/piinstaller/scripts/install-dsi-radio-setup.sh` (Pfad anpassen).
- Falls das Skript von Windows kopiert wurde: Zeilenumbrüche anpassen: `sed -i 's/\r$//' /pfad/.../install-dsi-radio-setup.sh`

Das Skript installiert `python3-gi`, `gir1.2-gstreamer-1.0`, `gstreamer1.0-plugins-good/bad`, `gstreamer1.0-pulseaudio` und **`gstreamer1.0-libav`** (für AAC, z. B. NDR 1) und richtet die Venv mit `--system-site-packages` ein.

**Wenn es danach immer noch nicht funktioniert:**

- AAC-Decoder prüfen:
  ```bash
  gst-inspect-1.0 avdec_aac
  ```
  Wenn „No such element“: Paket manuell installieren: `sudo apt install gstreamer1.0-libav`
- Venv nutzt System-Pakete: Das Skript baut die Venv unter `apps/dsi_radio/.venv` neu mit `--system-site-packages`. Falls du die App anders startest (z. B. systemweites Python), dort ebenfalls `python3-gi` und GStreamer-Pakete installiert haben.
- Ausgabegerät: Einstellungen → Sound → Ausgabegerät prüfen (z. B. Gehäuse-Lautsprecher statt HDMI).

**Logos werden nicht angezeigt:** Senderlogos kommen aus `stations.py` (logo_url) oder über das **Backend** (Logo-Proxy). Wenn das Backend nicht läuft (Port 8000), lädt die App Logos nur direkt von der Quelle – das kann fehlschlagen. Backend starten: im Projektroot `./start-backend.sh` oder als Service `sudo systemctl start pi-installer.service`. Außerdem: `apps/dsi_radio/stations.py` muss vorhanden sein (Senderliste inkl. Logo-URLs).

Die App ist eigenständig; Konfiguration (Favoriten, Theme, Anzeige) liegt unter `~/.config/pi-installer-dsi-radio/` und kann auch über die PI-Installer-Oberfläche (DSI-Radio Einstellungen) verwaltet werden.
