# Freenove 4,3″ TFT – PI-Installer Integration

## Erkennung

Der PI-Installer erkennt das Freenove-Gehäuse automatisch:

- **I2C-Expansion-Board:** Adresse `0x21` (Bus 0 oder 1), Register `0xfd` (REG_BRAND)
- **DSI-Display:** `wlr-randr` oder `/sys/class/drm/card*-DSI-*`
- **Audio:** `/proc/asound/cards` (Lautsprecher über System-Sound wählbar)

Wenn DSI oder Expansion-Board erkannt wird, erscheint im **App Store** der TFT-Bereich sowie der Menüpunkt **TFT Display** in der Sidebar.

## Lautsprecher

Die Gehäuse-Lautsprecher werden über die normalen System-Audio-Einstellungen genutzt:

- **Einstellungen → Sound** oder `pavucontrol` (Warnung „Unable to acquire accessibility bus“ unterdrücken: `GTK_A11Y=none pavucontrol`)
- **Ausgabegerät** auf die Freenove-Audio-Ausgabe stellen

Für Internetradio, Wecker usw. wird dann automatisch über die Gehäuse-Lautsprecher ausgegeben.

## TFT-Modi

Im PI-Installer unter **TFT Display** stehen Modi bereit:

- **Dashboard:** CPU, RAM, Temperatur
- **Internetradio:** Radio SAW, 1Live, WDR 2, WDR 4 – Senderlogo und Now-Playing auf dem DSI
- **Wecker:** Alarm auf dem Display (Implementierung folgt)
- **Bilderrahmen:** Fotos im Loop (Implementierung folgt)
- **NAS-Auslastung:** Speicher-Übersicht (Implementierung folgt)
- **Hauszentrale:** Smart-Home-Status (Implementierung folgt)
- **Leerlauf:** Uhr und Info (Implementierung folgt)

## Internetradio auf dem DSI anzeigen

### Empfohlen: Native PyQt6-App (kein Frontend nötig)

Die **standalone PyQt6-App** läuft ohne Web-Frontend und ohne dass `http://127.0.0.1:3001` erreichbar sein muss. Der Fenstertitel „PI-Installer DSI Radio“ wird von der Wayfire-Regel automatisch auf **DSI-1** gelegt – das Fenster erscheint also direkt auf dem Gehäuse-Display.

1. **Einmalig einrichten** (z. B. über das Install-Skript oder manuell):
   ```bash
   sudo bash scripts/install-freenove-tft-apps.sh
   ```
   Das Skript richtet u. a. die PyQt6-Umgebung unter `apps/dsi_radio/` ein.

   Oder nur DSI-Radio manuell (auf dem Pi):
   ```bash
   cd ~/Documents/PI-Installer
   ./scripts/install-dsi-radio-local.sh
   ```
   Oder einzeln: `cd apps/dsi_radio && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
   Optional: Audio-Player für Streams: `sudo apt install vlc` oder `sudo apt install mpv` (oder mpg123).

   **Vom Laptop aus auf dem Pi installieren** (SSH, Pi muss erreichbar sein):
   ```bash
   ./scripts/install-dsi-radio-on-pi.sh [PI-HOST]
   # z. B. PI_HOST=pi5-gg.local ./scripts/install-dsi-radio-on-pi.sh
   ```

2. **DSI-Radio starten:**
   ```bash
   ./scripts/start-dsi-radio.sh
   ```
   Das Skript startet zuerst die native App, falls PyQt6 vorhanden ist. Sonst Fallback auf Browser (siehe unten).

   Oder explizit nur die native App:
   ```bash
   ./scripts/start-dsi-radio-native.sh
   ```

3. **Wayfire-Regel:** Ohne Regel erscheint das DSI-Radio-Fenster beim Start oft auf HDMI. Mit `install-freenove-tft-apps.sh` oder `./scripts/ensure-dsi-window-rule.sh` wird in `~/.config/wayfire.ini` eingetragen:
   ```ini
   dsi_pi_installer = on created if (app_id is "pi-installer-dsi-radio") | (title contains "PI-Installer DSI") then start_on_output "DSI-1"
   ```
   **Wirkung:** Beim Erstellen des Fensters legt Wayfire es automatisch auf DSI-1 (TFT) – nicht auf HDMI. Die native App setzt den Wayland-`app_id` „pi-installer-dsi-radio“ (sofort beim Start); der Titel „PI-Installer DSI …“ dient als Fallback (z. B. für den Browser).

**Metadaten (Now Playing):** Wenn das Backend auf Port 8000 läuft, holt die App optional Titel/Interpret von dort. Ohne Backend wird „Live“ angezeigt – der Stream läuft trotzdem.

**Lautstärke:** Der Lautstärkeregler (rechts neben den Senderbuttons, oberhalb des Seitenumschalters) steuert die Ausgabe des aktiven Kanals: zuerst wird PulseAudio (`pactl set-sink-volume @DEFAULT_SINK@`) genutzt, falls nicht verfügbar ALSA (amixer Master/PCM). Bei fehlendem Ton: Ausgabegerät in den System-Einstellungen (Sound) auf die Freenove-Lautsprecher stellen.

**Oberfläche (ab 1.3.1.0):** Radioanzeige mit Logo links und schwarzem Klavierlack-Rahmen, darin grüne Anzeige mit schwarzer Schrift; D/A-Schiebeschalter (Digital/LED vs. Analog); analoge VU-Anzeige mit Skala 0–100 %; Uhr mit Datum.

---

### Fallback: Browser mit Web-Ansicht

Wenn die native App nicht installiert ist, startet `./scripts/start-dsi-radio.sh` einen Browser mit der Web-Ansicht. Dafür müssen **Backend (Port 8000) und Frontend (Port 3001)** laufen.

1. **Backend und Frontend starten:**
   ```bash
   ./start-backend.sh    # Terminal 1
   ./start-frontend.sh   # Terminal 2
   ```

2. **DSI-Radio starten:**
   ```bash
   ./scripts/start-dsi-radio.sh
   ```
   Öffnet einen Browser mit `http://127.0.0.1:3001/?view=dsi-radio`. Das Fenster erscheint oft zuerst auf HDMI.

3. **Fenster auf DSI verschieben:**
   - **Manuell:** Fenster mit der Maus auf das DSI-Display ziehen.
   - **Wayfire:** Dieselbe Fensterregel wie oben – Titel der App/Browser so setzen, dass er „PI-Installer DSI“ enthält (z. B. Chromium mit `--app=...` und passendem Fenstertitel), oder Fenster nach dem Öffnen auf DSI ziehen.

4. **Direkte URL** (wenn Frontend läuft):
   ```
   http://127.0.0.1:3001/?view=dsi-radio
   ```

**Hinweis:** Wenn die Website unter `http://127.0.0.1:3001` nicht erreichbar ist (Frontend nicht gestartet oder falsche Adresse), die **native PyQt6-App** nutzen – sie benötigt kein Frontend.

## Gehäuse wird nicht erkannt

1. **API direkt prüfen:** `curl http://localhost:8000/api/system/freenove-detection` – zeigt `expansion_board`, `dsi_display`, `audio_available`.
2. **I2C:** Benutzer in Gruppe `i2c`: `sudo usermod -aG i2c $USER`, dann abmelden/anmelden. Prüfen: `i2cget -y 1 0x21 0xfd` (sollte einen Hex-Wert ausgeben).
3. **i2c-tools:** Falls fehlend: `sudo apt install i2c-tools`. I2C in `raspi-config` (Interface Options) aktivieren.
4. **DSI:** `/sys/class/drm/card*-DSI-*/status` sollte `connected` enthalten, wenn das DSI-Display verbunden ist.

## Installation (alles auf einmal)

Das Skript richtet I2C, Fensterregeln, Desktop-Verknüpfung und Pakete ein:

```bash
cd /pfad/zu/PI-Installer
sudo bash scripts/install-freenove-tft-apps.sh
```

Danach: abmelden/anmelden, PI-Installer starten, DSI Radio über Desktop-Icon oder „Auf DSI anzeigen“-Button.

**Kein Sound?** (1) Klick auf „Abspielen“. (2) **Einstellungen → Sound:** Ausgabegerät auf **Gehäuse-Lautsprecher** (Freenove) stellen – der Player nutzt das Standard-Ausgabegerät. (3) Backend optional (nur für Metadaten). (4) Bei Fehlermeldung: Audio-Treiber prüfen (`aplay -l`).

**App startet auf HDMI statt DSI?** Wayfire-Regel anlegen: `./scripts/ensure-dsi-window-rule.sh` (als Benutzer), danach abmelden/anmelden oder Wayfire neu starten. Auf manchen Setups (z. B. Raspberry Pi mit DSI+HDMI) greift `start_on_output` trotzdem nicht zuverlässig. **Workaround:** Fenster nach dem Start mit der Maus auf das DSI-Display ziehen, oder in Wayfire mit **Super+O** („next output with window“) Fenster auf den nächsten Ausgang verschieben – mehrfach drücken, bis es auf DSI-1 ist.

**DSI im Portrait (transform 90)?** Die native App startet standardmäßig mit Fenstergröße 480×800. Über Umgebungsvariable abschaltbar: `PI_INSTALLER_DSI_PORTRAIT=0 ./scripts/start-dsi-radio.sh`.

**DSI-Button / Fenster auf HDMI:** Link öffnet neues Fenster. Fenster per Maus auf DSI ziehen oder **Super+O** nutzen, bis es auf DSI-1 erscheint.
