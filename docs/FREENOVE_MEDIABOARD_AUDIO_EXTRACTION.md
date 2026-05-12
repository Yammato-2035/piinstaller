# Problem: Mediaboard extrahiert kein Audio von HDMI

## Wie Gehäuselautsprecher und DSP1 zusammenhängen

Die **Gehäuselautsprecher** (und Kopfhörerbuchse) werden vom **DSP1** auf dem Mediaboard angesteuert. Der **Ton muss auf dem DSP1 abgespielt werden**, damit die Gehäuselautsprecher Ton abgeben. Der DSP1 erhält sein Signal vom Mediaboard, das Audio **passiv** aus dem HDMI-Signal eines der Pi-HDMI-Ports extrahiert. In der Software wählst du dafür den **richtigen HDMI-Sink** (107c701400 oder 107c706400) als Standard-Ausgang – je nach Board ist der eine oder andere Port intern mit dem Mediaboard/DSP1 verbunden.

## Symptom

Beide HDMI-Sinks (`alsa_output.platform-107c701400.hdmi.hdmi-stereo` und `alsa_output.platform-107c706400.hdmi.hdmi-stereo`) führen Audio nur zum HDMI-Monitor, nicht zu den Gehäuselautsprechern.

## Mögliche Ursachen

### 1. HDMI-Sinks sind SUSPENDED

**WICHTIG:** Wenn beide HDMI-Sinks SUSPENDED sind, müssen sie aktiviert werden, bevor das Mediaboard Audio extrahieren kann.

**Lösung:**
```bash
# Aktiviere beide HDMI-Sinks:
./scripts/activate-hdmi-sinks.sh

# Oder manuell:
pactl set-default-sink alsa_output.platform-107c701400.hdmi.hdmi-stereo
pactl set-sink-mute alsa_output.platform-107c701400.hdmi.hdmi-stereo 0
pactl set-sink-volume alsa_output.platform-107c701400.hdmi.hdmi-stereo 70%

# Dann Audio abspielen (aktiviert den Sink):
paplay /usr/share/sounds/alsa/Front_Left.wav
```

### 2. Mediaboard nicht richtig angeschlossen

Das Mediaboard ist über ein FPC-Kabel (Flachbandkabel) mit der PCIe-Schnittstelle verbunden. Es erscheint **nicht** als separates PCIe-Audio-Gerät, da es Audio passiv aus HDMI extrahiert. Prüfe die Verbindung:

```bash
# Prüfe PCIe-Geräte:
lspci | grep -i audio

# Prüfe PCIe-Verbindungen:
lspci -v | grep -A10 -i "audio\|multimedia"
```

**Lösung:** 
- Prüfe das FPC-Kabel zwischen Pi 5 und Mediaboard
- Stelle sicher, dass das Mediaboard richtig im Gehäuse sitzt
- Prüfe die PCIe-Verbindung

### 2. Mediaboard extrahiert nur ohne Monitor

Das Mediaboard könnte Audio nur extrahieren, wenn kein Monitor angeschlossen ist.

**Test:**
```bash
# Monitor abstecken und testen:
./scripts/test-audio-without-monitor.sh
```

**Lösung:** Falls das funktioniert, ist das Mediaboard möglicherweise so konfiguriert, dass es nur ohne Monitor funktioniert.

### 3. Mediaboard benötigt spezielle Initialisierung

Das Mediaboard könnte eine spezielle Initialisierung benötigen, die nicht automatisch erfolgt.

**Prüfe:**
```bash
# Prüfe Kernel-Logs (benötigt sudo):
sudo dmesg | grep -i "audio\|hdmi\|pcie\|freenove" | tail -50

# Prüfe System-Logs:
journalctl -k | grep -i "audio\|hdmi\|pcie" | tail -50
```

### 4. Hardware-Problem

Das Mediaboard könnte defekt sein oder die Lautsprecher-Verbindungen sind nicht korrekt.

**Prüfe:**
- Sind die Lautsprecher richtig am Mediaboard angeschlossen?
- Falls das Gehäuse einen MUTE-Schalter hat: ist er aus? (Nicht bei allen Freenove-Gehäusen vorhanden.)
- Gibt es sichtbare Schäden am Mediaboard?

### 5. Audio-Routing-Problem

Das Mediaboard könnte Audio von einem anderen Port oder auf eine andere Weise extrahieren müssen.

**Mögliche Lösungen:**

1. **Prüfe ob es ein separates Audio-Gerät gibt:**
   ```bash
   ./scripts/diagnose-pi-audio-outputs.sh
   ```

2. **Teste direkt über ALSA (ohne PipeWire):**
   ```bash
   ./scripts/test-alsa-direct-freenove.sh
   ```

3. **Prüfe ob das Mediaboard als separates Gerät erscheint:**
   ```bash
   pactl list cards
   pactl list sinks
   ```

## Diagnose-Skript

Führe das Diagnose-Skript aus, um alle relevanten Informationen zu sammeln:

```bash
./scripts/diagnose-mediaboard-connection.sh
```

Dieses Skript prüft:
- PCIe-Verbindung des Mediaboards
- HDMI-Port-Status
- ALSA-Karten
- PipeWire-Sinks
- Freenove I2C-Expansion-Board
- MUTE/Stummschaltung (falls am Gehäuse vorhanden)

**WICHTIGER BEFUND:** Wenn beide HDMI-Sinks **SUSPENDED** sind, müssen sie aktiviert werden:

```bash
./scripts/activate-hdmi-sinks.sh
```

Dieses Skript:
- Setzt beide HDMI-Sinks als Standard-Sink (aktiviert sie)
- Hebt Stummschaltung auf
- Setzt Lautstärke auf 70%
- Spielt Test-Ton ab (aktiviert den Sink)

## Nächste Schritte

1. **Führe Diagnose-Skript aus:**
   ```bash
   ./scripts/diagnose-mediaboard-connection.sh
   ```

2. **Prüfe Hardware-Verbindungen:**
   - FPC-Kabel zwischen Pi 5 und Mediaboard
   - Lautsprecher-Verbindungen am Mediaboard
   - Falls Gehäuse MUTE-Schalter hat: prüfen

3. **Teste ohne Monitor:**
   ```bash
   # Monitor abstecken
   ./scripts/test-audio-without-monitor.sh
   ```

4. **Prüfe Kernel-Logs:**
   ```bash
   sudo dmesg | grep -i "audio\|hdmi\|pcie\|freenove" | tail -50
   ```

5. **Kontaktiere Freenove Support:**
   - Falls alle Software-Lösungen fehlschlagen, könnte es ein Hardware-Problem sein
   - Freenove Support: https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md` – Allgemeine Troubleshooting-Dokumentation
- `docs/FREENOVE_AUDIO_OLED_SENSORS.md` – Technische Details zum Mediaboard
- `docs/HDMI_A1_SINK_PROBLEM.md` – Problem mit HDMI-A-1 Sink-Erstellung
