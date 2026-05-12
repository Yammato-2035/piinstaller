# Freenove Case: LEDs im Rhythmus der Musik (audio-reaktiv)

Die RGB-LEDs des **Freenove Computer Case Kit Pro** (Erweiterungsplatine I2C 0x21) haben eingebaute Modi (Rainbow, Breathing, Following, RGB), aber **keinen** eingebauten „Musik“-Modus. Damit die Lüfter-LEDs zum Rhythmus der Musik flackern, muss man:

1. **Audio** erfassen (System-Ausgabe oder Mikrofon),
2. **Lautstärke** (oder Frequenzanteile) auswerten,
3. **LED-Farben/Helligkeit** per I2C an die Erweiterungsplatine senden.

---

## Technik der Freenove-LED-Steuerung

Die Erweiterungsplatine wird per **I2C** (Adresse **0x21**, Bus 1) angesprochen. Relevant aus `api_expansion.py`:

| Register (Write) | Funktion |
|------------------|----------|
| `REG_LED_ALL = 0x02` | Alle LEDs auf eine Farbe: `[R, G, B]` (0–255) |
| `REG_LED_SPECIFIED = 0x01` | Einzelne LED: `[led_id, R, G, B]` |
| `REG_LED_MODE = 0x03` | Modus: 0=aus, 1=RGB, 2=Following, 3=Breathing, 4=Rainbow |

Für **musikgesteuerte** Effekte:

- **Modus 1 (RGB)** setzen, danach in einer Schleife (z. B. 30–60× pro Sekunde) `set_all_led_color(r, g, b)` mit Werten aufrufen, die aus der aktuellen Lautstärke (oder FFT) berechnet werden.
- So „flackern“ die LEDs mit der Musik (z. B. lauter = heller/andere Farbe).

---

## Audio-Quelle

Damit das Skript die **abgespielte Musik** sieht, braucht es eine **Eingabequelle**, die den System-Ton liefert:

### Option A: PulseAudio/PipeWire – Monitor des Standard-Sinks

- Jeder **Sink** (Lautsprecher-Ausgabe) hat eine **Monitor-Quelle**, die den Ton abgreift.
- In **pavucontrol** (oder Einstellungen → Sound):  
  Reiter **Eingabe** → unter „Alle Anwendungen“ die **Monitor-Quelle** des gewünschten Sinks wählen (z. B. „Monitor of … HDMI …“).
- Oder: **Standard-Eingabegerät** auf „Monitor of [Name des Ausgabegeräts]“ setzen.  
  Dann liest das Skript beim **Standard-Eingabegerät** genau den Ton, der aus den Lautsprechern kommt.

### Option B: Mikrofon

- Wenn kein Monitor verfügbar ist: **Mikrofon** als Eingabe nutzen. Die LEDs reagieren dann auf den Raumton (inkl. Musik aus den Lautsprechern). Latenz und Rückkopplung beachten.

---

## Ablauf (Beispiel)

1. **Audio-Stream** vom Standard-Eingabegerät lesen (z. B. 1024 Samples bei 16 kHz).
2. **Pegel** berechnen (z. B. RMS oder Peak).
3. **Farbe/Helligkeit** daraus ableiten (z. B. `value = min(255, int(pegel * Faktor))` → `set_all_led_color(value, value, value)` für weißes Flackern, oder Bass = Rot, Mitten = Grün usw. mit FFT).
4. **I2C:** `set_led_mode(1)` einmal, dann in der Schleife `set_all_led_color(r, g, b)`.
5. Kurz **warten** (z. B. 1/30 s), dann wieder von vorne.

---

## Beispielskript

Im Projekt liegt ein **Beispielskript**, das genau das umsetzt:

- **Skript:** `scripts/led-music-reactive.py`
- **Voraussetzungen:** I2C aktiviert, Benutzer in Gruppe `i2c`, Python3 mit `smbus`, `numpy`, `sounddevice`.
- **Verwendung:** Siehe Kommentare im Skript und Abschnitt unten.

Details und Optionen (Lautstärke-Skalierung, Farben, FFT) stehen im Skript und können dort angepasst werden.

---

## Voraussetzungen auf dem Pi

1. **I2C** aktiviert (`sudo raspi-config` → Interface Options → I2C).
2. Benutzer in Gruppe **i2c** (für Zugriff ohne root):
   ```bash
   sudo usermod -aG i2c "$USER"
   ```
   Danach abmelden/anmelden oder Neustart.
3. **Python-Pakete (virtuelle Umgebung empfohlen):**  
   Unter Raspberry Pi OS / Debian ist die System-Python-Umgebung „externally managed“ – Pakete wie `numpy` und `sounddevice` sollten in einer **venv** installiert werden, nicht mit `pip install --user` oder systemweit.

   **Einmalig einrichten** (im Projektverzeichnis, dort wo der Ordner `scripts/` liegt):
   ```bash
   ./scripts/setup-led-music-venv.sh
   ```
   Das Skript erstellt eine venv unter `scripts/venv-led-music/` **mit `--system-site-packages`**, damit das per apt installierte Modul **smbus** (`python3-smbus`) in der venv sichtbar ist. Außerdem wird **libportaudio2** (PortAudio-Bibliothek für `sounddevice`) per apt installiert. In der venv werden nur `numpy` und `sounddevice` per pip installiert.

   **Ohne Setup-Skript (manuell):** Die venv muss mit **`--system-site-packages`** erstellt werden, damit `smbus` (von `python3-smbus`) verfügbar ist:
   ```bash
   sudo apt install -y python3-smbus python3-venv python3-full
   cd scripts   # innerhalb des PI-Installer-Projektverzeichnisses
   python3 -m venv --system-site-packages venv-led-music
   venv-led-music/bin/pip install --upgrade pip
   venv-led-music/bin/pip install numpy sounddevice
   ```
   **Falls bereits eine venv ohne System-Pakete existiert** und „No module named 'smbus'“ erscheint: venv löschen und neu anlegen: `rm -rf scripts/venv-led-music && ./scripts/setup-led-music-venv.sh`
4. **Audio-Eingabe:** Wie oben beschrieben Standard-Eingabe auf „Monitor of …“ setzen (oder Mikrofon), damit das Skript den abgespielten Ton sieht.

---

## Start des Beispielskripts

**Mit venv** (nach `./scripts/setup-led-music-venv.sh`):
```bash
./scripts/venv-led-music/bin/python scripts/led-music-reactive.py
```
(Aus dem PI-Installer-Projektverzeichnis.)

**Falls „Error querying device -1“ erscheint:** Es ist kein gültiges Standard-**Eingabegerät** gesetzt.  
- Eingabegeräte anzeigen: `./scripts/venv-led-music/bin/python scripts/led-music-reactive.py --list-devices`  
- In **pavucontrol** (oder Einstellungen → Sound): Reiter **Eingabe** → Standard-Eingabegerät auf **„Monitor of [Ihr Lautsprecher]“** setzen (dann erfasst das Skript den abgespielten Ton).  
- Oder ein bestimmtes Gerät verwenden: `... led-music-reactive.py --device 2` (Index aus `--list-devices`).

**Ohne venv** (nur wenn `numpy` und `sounddevice` bereits installiert sind, z. B. in einer anderen venv):
```bash
python3 scripts/led-music-reactive.py
```

Mit **Strg+C** beendet man das Skript. Die LEDs bleiben in dem Zustand, in dem sie beim Beenden waren; um wieder einen Standard-Modus zu nutzen, die Freenove-Steuerungs-App verwenden oder ein kleines Skript, das z. B. `set_led_mode(4)` (Rainbow) setzt.

---

## Erweiterungen

- **FFT:** Statt nur Gesamtlautstärke können **Frequenzbänder** (Bass, Mitten, Höhen) ausgewertet und unterschiedlichen Farben zugeordnet werden (z. B. `numpy.fft`, `scipy.signal`).
- **Einzelne LEDs:** Wenn die Anzahl der LEDs bekannt ist, kann `set_led_color(led_id, r, g, b)` genutzt werden, um z. B. verschiedene Bereiche (links/rechts, unten/oben) unterschiedlich anzusteuern.
- **Dauerhaft beim Start:** Skript als **systemd-User-Service** oder über die Freenove-**Custom-LED-Task** (task_led.py durch ein musikreaktives Skript ersetzen) starten – siehe Freenove-Doku „Settings → Create Service“ bzw. „Custom“-Modus.

---

## Referenzen

- **Freenove-Repo:** https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi (u. a. `Code/api_expansion.py`)
- **Freenove-Doku (APP Control, LED):** https://docs.freenove.com/projects/fnk0107/en/latest/fnk0107/codes/tutorial/4_APP_Control.html
- **Projekt-Doku:** `docs/FREENOVE_AUDIO_OLED_SENSORS.md` (Register-Übersicht), `docs/FREENOVE_COMPUTER_CASE.md` (Zusammenbau, I2C, Software)
