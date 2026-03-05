# Freenove Case: Audio (Gehäuselautsprecher), OLED, Sensoren

Auswertung des offiziellen Freenove-Repositories (FNK0107 / Computer Case Kit Pro für Raspberry Pi 5):

- **Repository:** https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi  
- **Code:** `Code/api_expansion.py`, `Code/api_oled.py`, `Code/api_systemInfo.py`, `Code/task_oled.py`

---

## 1. Gehäuselautsprecher (Audio)

### Technik des Freenove Mediaboards

Das **Freenove Computer Case Kit Pro (FNK0107)** hat ein **Audio-Video-Board (Case Adapter Board)**, das:
- **Audio aus HDMI-Signalen extrahiert** (Raspberry Pi 5 hat keinen 3,5-mm-Ausgang mehr)
- Audio über **3,5-mm-Ausgang** und **Gehäuselautsprecher** ausgibt
- Eine **Audio-Verstärkungsschaltung** für zwei 4Ω/3W-Lautsprecher enthält
- Optional einen **MUTE-Schalter** zum Ein-/Ausschalten der Lautsprecher hat (nicht bei allen Gehäusen)

### Befund im Freenove-Repository

- Es gibt **keine** eigene API oder Initialisierung für die Gehäuselautsprecher im Code.
- Das **Audio-Video-Board** liefert Audio über die **normale System-Ausgabe** (PulseAudio/PipeWire/ALSA).
- Die Lautsprecher sind also kein separates I2C-/Software-„Gerät", sondern hängen an derselben Karte wie HDMI/3,5-mm (je nach Verdrahtung).

### Automatische Konfiguration (Empfohlen)

**PI-Installer bietet zwei Skripte:**

1. **Diagnose-Skript** – Analysiert alle Audio-Geräte:
   ```bash
   ./scripts/diagnose-freenove-audio.sh
   ```
   Zeigt alle verfügbaren ALSA-Karten, PulseAudio/PipeWire Sinks und sucht nach Freenove-spezifischen Gerätenamen.

2. **Konfigurations-Skript** – Findet und konfiguriert automatisch das Mediaboard:
   ```bash
   # Analyse (ohne Änderungen):
   ./scripts/configure-freenove-audio.sh --dry-run
   
   # Konfiguration ausführen:
   ./scripts/configure-freenove-audio.sh
   ```
   Das Skript:
   - Findet automatisch den richtigen Audio-Sink (Priorität: Speaker > Headphone > Analog > Non-HDMI)
   - Setzt ihn als Standard-Sink
   - Prüft und erhöht ggf. die Lautstärke
   - Hebt Stummschaltung auf

3. **HDMI-Audio ohne Monitor aktivieren** (WICHTIG für Freenove):
   ```bash
   # Prüft und konfiguriert HDMI-Audio:
   ./scripts/configure-freenove-hdmi-audio.sh
   
   # Aktiviert HDMI-Audio auch ohne Monitor (erfordert Neustart):
   sudo ./scripts/enable-hdmi-audio-without-monitor.sh [HDMI-Port]
   # Beispiel: sudo ./scripts/enable-hdmi-audio-without-monitor.sh HDMI-A-1
   ```
   **Warum wichtig?** Das Mediaboard extrahiert Audio aus HDMI. Wenn kein Monitor erkannt wird, wird HDMI-Audio deaktiviert → kein Ton aus den Gehäuselautsprechern.

### Manuelle Konfiguration

Falls die automatische Konfiguration nicht funktioniert:

1. **Einstellungen → Sound** (oder `pavucontrol`):  
   **Ausgabegerät** auf die gewünschte Quelle stellen:
   - Wenn ein Eintrag wie **„Gehäuse-Lautsprecher"** oder **„Headphones"** (am Case) erscheint → diesen wählen.
   - Wenn nur **HDMI**-Ausgänge (z. B. vc4hdmi0, vc4hdmi1) sichtbar sind, sind die Gehäuselautsprecher oft an **einen** dieser Ausgänge angebunden; dann den passenden HDMI-Ausgang wählen (laut Freenove-Dokumentation ggf. der 3,5-mm-Ausgang am Board).

2. **DSI-Radio / PI-Installer:**  
   Die App nutzt das **aktuelle Standard-Ausgabegerät** (`pactl get-default-sink`). Sobald in den Systemeinstellungen „Gehäuse-Lautsprecher" (oder der richtige HDMI-Ausgang) als Standard gesetzt ist, geht der Ton dorthin – also auch zu den Gehäuselautsprechern, wenn sie mit diesem Gerät verbunden sind.

3. **Manuell prüfen:**
   ```bash
   pactl get-default-sink
   pactl list short sinks
   aplay -l
   ```
   Wenn ein Gerät nur unter ALSA erscheint, aber nicht unter Pulse/PipeWire, muss ggf. der entsprechende Treiber/Konfiguration (z. B. für 3,5-mm am Freenove-Board) aktiv sein.

### Troubleshooting

**Kein Ton aus den Gehäuselautsprechern:**

1. **HDMI-Audio muss aktiv sein:** Das Mediaboard extrahiert Audio aus HDMI. Wenn kein HDMI-Monitor angeschlossen ist, kann HDMI-Audio deaktiviert sein.
   - **Prüfen:** `wpctl status` sollte HDMI-Sinks zeigen
   - **Lösung:** In `/boot/firmware/cmdline.txt` ergänzen: `video=HDMI-A-1:e` (oder `video=HDMI-A-1:1920x1080@60D` für fixe Auflösung)
   - **Welcher Port?** Prüfe mit: `ls /sys/class/drm/ | grep HDMI`
   - **Skript:** `./scripts/configure-freenove-hdmi-audio.sh` prüft und konfiguriert automatisch

2. **Richtiger HDMI-Port:** Das Mediaboard extrahiert Audio nur von einem bestimmten HDMI-Port (HDMI-A-1 oder HDMI-A-2).
   - **Problem:** Wenn ein Monitor auf HDMI1 angeschlossen ist, könnte das Mediaboard von HDMI0 extrahieren müssen (oder umgekehrt).
   - **Lösung:** Teste beide HDMI-Ports: `./scripts/test-freenove-hdmi-ports.sh`
   - **Hinweis:** Der Ton sollte aus den **Gehäuselautsprechern** kommen, nicht aus dem HDMI-Monitor!

3. **Standard-Sink prüfen:** Der Standard-Sink sollte auf den richtigen HDMI-Port gesetzt sein
   - **Prüfen:** `wpctl status` zeigt Standard-Sink unter "Default Configured Devices"
   - **Setzen:** `wpctl set-default <HDMI-Sink-ID>` oder `pactl set-default-sink <HDMI-Sink-Name>`
   - **Skript:** `./scripts/configure-freenove-default-sink.sh` konfiguriert automatisch

4. **Lautsprecher-Verbindungen:** Sind die Lautsprecher physisch korrekt am "SPEAKER"-Header des Case-Adapter-Boards angeschlossen?

5. **3,5-mm-Test:** Teste den 3,5-mm-Ausgang am Case-Board. Wenn dort auch kein Ton kommt, ist HDMI-Audio wahrscheinlich nicht aktiv oder der falsche Port verwendet.

6. **Diagnose ausführen:** `./scripts/diagnose-freenove-audio.sh` oder `./scripts/diagnose-pi-audio-outputs.sh`

7. **Audio-Test:** `paplay /usr/share/sounds/alsa/Front_Left.wav` oder `speaker-test -c 2 -t sine -f 1000`

**WICHTIG:** Das Mediaboard extrahiert Audio **passiv** aus HDMI. Wenn HDMI-Audio nicht aktiv ist (z. B. weil kein Monitor erkannt wird), gibt es nichts zum Abgreifen → keine Tonausgabe über die Gehäuselautsprecher.

**BEKANNTES PROBLEM:** Wenn beide HDMI-Ports nur Ton zum Monitor ausgeben, nicht zu den Gehäuselautsprechern:
- Siehe `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md` für detaillierte Lösungsansätze
- Möglicherweise funktioniert das Mediaboard nur ohne angeschlossenen Monitor
- Prüfe Hardware-Verbindungen (Lautsprecher am SPEAKER-Header, PCIe-Verbindung)
- Teste den 3,5-mm-Ausgang am Case-Board

**Falls PulseAudio/PipeWire nicht installiert ist:**
```bash
sudo apt update
sudo apt install -y pulseaudio-utils pavucontrol wireplumber
```

**Kurz:** Lautsprecher werden **nicht** per Code „initialisiert", sondern über die **System-Sound-Einstellungen** (Standard-Ausgabegerät) gesteuert. Das Mediaboard extrahiert Audio automatisch aus HDMI-Signalen, **aber nur wenn HDMI-Audio aktiv ist**.

---

## 2. OLED-Display (0,96″) – Sensordaten anzeigen

### Technik (aus dem Freenove-Repo)

- **Bibliothek:** `luma.oled` (SSD1306)
- **I2C:** Bus 1, Adresse **0x3C**
- **Installation:**  
  `sudo apt install python3-luma.oled`  
  I2C muss aktiviert sein (`raspi-config` → Interface Options → I2C).

### Verwendung im Freenove-Code

- **`api_oled.py`:** Klasse `OLED` – `draw_text()`, `draw_progress_bar()`, `draw_dial()`, `draw_circle_with_percentage()`, `clear()`, `show()` usw.
- **`task_oled.py`:** Zeigt wechselnde Bildschirme mit:
  - **Screen 1:** Datum, Wochentag, Uhrzeit  
  - **Screen 2:** IP, CPU-, Speicher-, Festplattenauslastung (Prozent)  
  - **Screen 3:** **Pi-Temperatur** (CPU) und **Gehäuse-Temperatur** (von der Erweiterungsplatine)  
  - **Screen 4:** Lüfter-Duty (Pi + Erweiterungsplatine)

Beispiel (nur Text auf OLED, ohne Freenove-Konfig):

```python
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=1)  # 180° = rotate=1
buffer = Image.new('1', (device.width, device.height))
draw = ImageDraw.Draw(buffer)
font = ImageFont.load_default()
draw.text((0, 0), "CPU: 45°C", font=font, fill="white")
draw.text((0, 16), "Case: 32°C", font=font, fill="white")
device.display(buffer)
```

Sensordaten dafür kommen von der Erweiterungsplatine (Temperatur) und von `api_systemInfo` (CPU, Speicher, Lüfter) – siehe Abschnitt 3.

---

## 3. Sensoren im Gehäuse abfragen

### Erweiterungsplatine (I2C, Adresse 0x21) – `api_expansion.py`

| Funktion            | Register (Read) | Beschreibung                    |
|---------------------|----------------|---------------------------------|
| **Temperatur**      | 0xfc (`REG_TEMP_READ`) | Gehäuse-/Board-Temperatur |
| Lüfter-Modus        | 0xf7           | 0=aus, 1=manuell, 2=Temp, 3=Pi-PWM |
| Lüfter-Duty         | 0xf9 (3 Bytes)| Duty für bis zu 3 Lüfter        |
| Lüfter-Drehzahl     | 0xf2 (10 Bytes) | Motor-RPM (5 Werte)           |
| LED-Modus           | 0xf6           | 0=aus, 1=RGB, 2=Following, 3=Breathing, 4=Rainbow |
| Temperatur-Schwellen| 0xfb           | für Lüfter-Steuerung           |
| Brand/Version       | 0xfd, 0xfe     | Erkennung Freenove-Board       |

Beispiel Temperatur auslesen (wie im Freenove-Repo):

```python
import smbus
bus = smbus.SMBus(1)
addr = 0x21
REG_TEMP_READ = 0xfc
temp = bus.read_byte_data(addr, REG_TEMP_READ)  # °C
bus.close()
```

### System (Raspberry Pi) – `api_systemInfo.py`

| Daten        | Quelle |
|-------------|--------|
| **CPU-Temperatur** | `/sys/devices/virtual/thermal/thermal_zone0/temp` (Wert / 1000 = °C) |
| **Lüfter-PWM (Pi)** | `/sys/devices/platform/cooling_fan/hwmon/hwmon*/pwm1` (0–255) |
| CPU-/RAM-/Disk-Nutzung | `psutil` |
| IP, Datum, Uhrzeit | Standard-Python / `socket` |

Zusammenfassung: **Gehäuse-Temperatur** und Lüfter kommen von der **Erweiterungsplatine (I2C 0x21)**, **CPU-Temperatur** und Systeminfos vom **Pi (sysfs/psutil)**. Das OLED kann mit `luma.oled` und diesen Werten beliebige Sensordaten anzeigen (wie in `task_oled.py`).
