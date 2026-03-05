# Problem: Mediaboard extrahiert kein Audio – Finale Analyse

**WICHTIG:** Siehe auch `docs/FREENOVE_AUDIO_DEEP_ANALYSIS.md` für eine umfassende Analyse der bekannten Raspberry Pi 5 HDMI-Audio-Regressionen und warum Audio früher funktionierte (Version 1.2.x.x).

## Symptom

**Beide HDMI-Sinks führen Audio nur zum Monitor, nicht zu den Gehäuselautsprechern.**

- ✅ Beide HDMI-Sinks sind verfügbar und funktionieren
- ✅ Audio wird korrekt ausgegeben
- ❌ Audio kommt nur aus dem HDMI-Monitor
- ❌ Kein Audio aus den Gehäuselautsprechern

## Diagnose-Ergebnisse

1. **PCIe-Verbindung:** Mediaboard wird nicht als separates PCIe-Audio-Gerät erkannt (erwartet, da passiv)
2. **Freenove Expansion-Board:** ✅ Erkannt (I2C-Bus 1, Adresse 0x21)
3. **HDMI-Sinks:** ✅ Beide verfügbar (Card 0 und Card 1)
4. **HDMI-Port-Status:**
   - HDMI-A-1: connected, disabled
   - HDMI-A-2: connected, enabled
5. **ALSA-Karten:** ✅ Beide vorhanden (vc4hdmi0 und vc4hdmi1)

## Mögliche Ursachen

### 1. Mediaboard extrahiert nur ohne Monitor (Wahrscheinlichste Ursache)

Das Mediaboard könnte so konfiguriert sein, dass es Audio nur extrahiert, wenn **kein Monitor angeschlossen** ist.

**Test:**
```bash
# Monitor abstecken
# Dann testen:
./scripts/test-audio-without-monitor.sh

# Oder manuell:
pactl set-default-sink alsa_output.platform-107c701400.hdmi.hdmi-stereo
paplay /usr/share/sounds/alsa/Front_Left.wav
```

**Falls das funktioniert:** Das Mediaboard ist so konfiguriert, dass es nur ohne Monitor funktioniert. Dies ist eine Hardware-Limitierung.

### 2. MUTE-Schalter aktiviert (nur falls am Gehäuse vorhanden)

Nicht bei allen Freenove-Gehäusen vorhanden. Falls vorhanden: Der MUTE-Schalter am Gehäuse könnte aktiviert sein.

**Prüfe:**
- Falls das Gehäuse einen MUTE-Schalter hat: Ist er in der richtigen Position?
- Ist der Schalter nicht versehentlich aktiviert?

### 3. Lautsprecher-Verbindungen

Die Lautsprecher könnten nicht richtig am Mediaboard angeschlossen sein.

**Prüfe:**
- Sind die Lautsprecher richtig am "SPEAKER"-Header des Mediaboards angeschlossen?
- Sind die Kabel richtig orientiert (Polarität)?
- Gibt es lose Verbindungen?

### 4. FPC-Kabel-Problem

Das FPC-Kabel zwischen Pi 5 und Mediaboard könnte nicht richtig angeschlossen sein.

**Prüfe:**
- Ist das FPC-Kabel richtig orientiert?
- Kontaktseite zum aktiven Cooler (Pi 5)
- Kontaktseite nach unten (Mediaboard)
- Siehe: `docs/FREENOVE_COMPUTER_CASE.md` – Abschnitt "Flachbandkabel (FPC) – Orientierung"

### 5. Hardware-Problem

Das Mediaboard könnte defekt sein.

**Prüfe:**
- Gibt es sichtbare Schäden am Mediaboard?
- Funktionieren andere Komponenten des Gehäuses (LEDs, Lüfter, Display)?
- Teste mit einem anderen Mediaboard (falls verfügbar)

### 6. Audio-Routing-Problem

Das Mediaboard könnte Audio von einem anderen Port oder auf eine andere Weise extrahieren müssen.

**Mögliche Lösungen:**

1. **Teste ohne Monitor:**
   ```bash
   # Monitor abstecken
   ./scripts/test-audio-without-monitor.sh
   ```

2. **Teste direkt über ALSA:**
   ```bash
   # Teste Card 0 (HDMI-A-1):
   aplay -D hw:0,0 /usr/share/sounds/alsa/Front_Left.wav
   
   # Teste Card 1 (HDMI-A-2):
   aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Left.wav
   ```

3. **Prüfe 3,5-mm-Ausgang:**
   ```bash
   # Kopfhörer in 3,5-mm-Buchse stecken
   paplay /usr/share/sounds/alsa/Front_Left.wav
   ```

## Nächste Schritte

### Schritt 0: Setze WirePlumber-Konfiguration zurück (Wenn es früher funktioniert hat!)

**WICHTIG:** Falls Audio früher funktioniert hat (z.B. unter Wayland), könnte eine persistente Konfiguration das Problem verursachen.

```bash
# Setze WirePlumber-Konfiguration zurück:
./scripts/reset-wireplumber-audio-config.sh
```

Dieses Skript:
- Entfernt benutzerdefinierte WirePlumber-Konfigurationen
- Löscht persistente State-Dateien
- Startet WirePlumber neu
- Erstellt Backup der alten Konfiguration

**Nach dem Reset:**
```bash
# Teste Audio erneut:
./scripts/test-both-hdmi-sinks.sh
```

### Schritt 0: EDID für HDMI-A-1 erzwingen (NEUE LÖSUNG aus Foren!)

**WICHTIG:** Pi 5 erkennt HDMI-Audio nur, wenn das HDMI-Endgerät EDID präsentiert. Das Mediaboard könnte kein EDID präsentieren.

**Lösung:** EDID erzwingen:

```bash
# Erzwinge EDID für HDMI-A-1:
sudo ./scripts/fix-freenove-audio-edid.sh
sudo reboot
```

**Nach dem Neustart:**
```bash
# Prüfe ob Card 0 verfügbar ist:
pactl list short sinks | grep 107c701400

# Teste Audio:
./scripts/test-freenove-speakers-simple.sh
```

**Siehe:** `docs/FREENOVE_AUDIO_EDID_SOLUTION.md` für vollständige Erklärung.

### Schritt 1: Teste ohne Monitor (WICHTIGSTE LÖSUNG!)

**WICHTIG:** Das ist der wahrscheinlichste Grund! Viele Freenove Mediaboards extrahieren Audio nur, wenn kein Monitor angeschlossen ist.

```bash
# 1. Monitor abstecken
# 2. Teste Audio:
./scripts/test-audio-without-monitor.sh

# Oder manuell:
pactl set-default-sink alsa_output.platform-107c701400.hdmi.hdmi-stereo
pactl set-sink-mute alsa_output.platform-107c701400.hdmi.hdmi-stereo 0
pactl set-sink-volume alsa_output.platform-107c701400.hdmi.hdmi-stereo 70%
paplay /usr/share/sounds/alsa/Front_Left.wav
```

**Falls das funktioniert:** 
- ✅ Das Mediaboard funktioniert nur ohne Monitor
- ⚠️ Dies ist eine Hardware-Limitierung des Mediaboards
- 💡 **Workaround:** Verwende einen HDMI-Dummy-Plug oder einen Monitor ohne Audio-Unterstützung

### Schritt 1a: Teste direkt über ALSA (umgeht PipeWire/WirePlumber)

**WICHTIG:** Falls PipeWire/WirePlumber das Audio-Routing blockiert, teste direkt über ALSA:

```bash
# Teste beide ALSA-Karten direkt:
./scripts/test-audio-direct-alsa.sh
```

Dieses Skript:
- Umgeht PipeWire/WirePlumber komplett
- Testet beide ALSA-Karten direkt (Card 0 und Card 1)
- Prüft ob das Mediaboard Audio extrahiert, auch ohne PipeWire-Sink

**Falls das funktioniert:** Das Problem liegt bei PipeWire/WirePlumber-Konfiguration, nicht bei der Hardware.

### Schritt 1b: Aktiviere HDMI-A-1 Display

**WICHTIG:** HDMI-A-1 ist "disabled". Versuche es zu aktivieren:

```bash
# Aktiviere HDMI-A-1 Display (mit sudo):
sudo ./scripts/activate-hdmi-a1-display.sh

# Oder manuell:
echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled
systemctl --user restart wireplumber.service

# Prüfe Status:
cat /sys/class/drm/card2-HDMI-A-1/enabled

# Teste Audio:
./scripts/test-both-hdmi-sinks.sh
```

**Falls das nicht funktioniert:** Starte das System neu (cmdline.txt enthält bereits `video=HDMI-A-1:e`):
```bash
sudo reboot
```

**Falls das funktioniert:** Das Mediaboard benötigt beide HDMI-Ports aktiv.

### Schritt 2: Prüfe Hardware-Verbindungen

1. **MUTE-Schalter:** Falls am Gehäuse vorhanden – nicht aktiviert?
2. **Lautsprecher:** Prüfe Verbindungen am Mediaboard
3. **FPC-Kabel:** Prüfe Orientierung und Sitz

### Schritt 3: Prüfe Kernel-Logs

```bash
sudo dmesg | grep -i "audio\|hdmi\|pcie\|freenove" | tail -50
```

Suche nach Fehlermeldungen bezüglich Audio/HDMI/PCIe.

### Schritt 4: Kontaktiere Freenove Support

Falls alle Software-Lösungen fehlschlagen:

- **Freenove Support:** https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
- **Email:** support@freenove.com
- **Website:** https://www.freenove.com

## Bekannte Einschränkungen

- Das Mediaboard extrahiert Audio **passiv** aus HDMI
- Es gibt **keine** Software-API zur Steuerung der Lautsprecher
- Das Mediaboard erscheint **nicht** als separates Audio-Gerät im System
- Die Lautsprecher sind **nicht** über I2C steuerbar
- Das Mediaboard könnte nur ohne Monitor funktionieren (Hardware-Limitierung)

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md` – Allgemeine Troubleshooting-Dokumentation
- `docs/FREENOVE_MEDIABOARD_AUDIO_EXTRACTION.md` – Problem-Analyse
- `docs/FREENOVE_COMPUTER_CASE.md` – Hardware-Zusammenbau (FPC-Kabel)
- `docs/FREENOVE_AUDIO_OLED_SENSORS.md` – Technische Details zum Mediaboard
