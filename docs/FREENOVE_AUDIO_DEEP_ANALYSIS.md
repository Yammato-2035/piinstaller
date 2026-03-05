# Tiefenanalyse: Freenove Audio-Probleme & Raspberry Pi 5 HDMI-Audio-Regressionen

## Zusammenfassung der Recherche

Diese Analyse basiert auf umfassender Recherche in Foren, GitHub-Issues und Dokumentation zu:
- Freenove Computer Case Kit Pro (FNK0107) Audio-Problemen
- Raspberry Pi 5 HDMI-Audio-Regressionen
- Warum Audio früher funktionierte (Version 1.2.x.x) und jetzt nicht mehr

---

## 1. Bekannte Raspberry Pi 5 HDMI-Audio-Regressionen

### 1.1 PipeWire/WirePlumber "Dummy Output" Problem

**Symptom:**
- PipeWire zeigt nur "Dummy Output" (auto_null) statt HDMI-Sinks
- `pactl list sinks` zeigt nur `auto_null`
- `aplay -l` zeigt vc4hdmi0/vc4hdmi1, aber keine PipeWire-Sinks
- `raspi-config` Audio-Option kehrt sofort zurück ohne Wirkung

**Quellen:**
- Raspberry Pi Forums: "No HDMI audio Pi 5 / Bookworm, only Dummy Output sink" (Thread #383075)
- GitHub: raspberrypi/linux #5950, #5525, #6651
- Betrifft: Pi 5 + Raspberry Pi OS Bookworm

**Ursache:**
- WirePlumber erstellt keine PipeWire-Sinks für HDMI-Geräte
- ALSA-Geräte existieren, aber PipeWire-Session-Manager erkennt sie nicht
- Oft nach System-Updates (`apt upgrade`)

### 1.2 HDMI-Audio nur mit Monitor

**Symptom:**
- HDMI-Audio funktioniert nur, wenn ein Monitor angeschlossen ist
- Ohne Monitor: nur "Dummy Output"
- Mit Monitor: HDMI-Sinks erscheinen

**Quellen:**
- Raspberry Pi Forums: "Raspi 5 hdmi audio" (Thread #383491)
- GitHub: raspberrypi/firmware #1871
- Betrifft: Pi 5 ohne angeschlossenen Monitor

**Ursache:**
- Pi 5 benötigt EDID/Hotplug-Signal für HDMI-Audio
- Ohne Monitor: kein EDID → kein HDMI-Audio
- Lösung: EDID erzwingen (siehe unten)

### 1.3 IEC958-Format statt PCM

**Symptom:**
- HDMI-Audio-Gerät läuft im IEC958-Modus (S/PDIF)
- `aplay` schlägt fehl: "Sample format not available"
- Nur `IEC958_SUBFRAME_LE` verfügbar, kein PCM

**Quellen:**
- Raspberry Pi Forums: "how to enable hdmi audio kernel 5.15 w/vc4" (Thread #330349)
- Betrifft: vc4hdmi-Treiber auf Pi 5

**Ursache:**
- vc4hdmi-Treiber exponiert IEC958-Interface statt PCM
- PipeWire/WirePlumber kann IEC958 nicht korrekt verarbeiten

---

## 2. Warum es früher funktionierte (Version 1.2.x.x)

### 2.1 System-Updates brechen HDMI-Audio

**Bekannte Regressionen nach Updates:**

1. **PipeWire/WirePlumber-Updates:**
   - Nach `apt upgrade` verschwinden HDMI-Sinks
   - Nur "Dummy Output" bleibt
   - Betrifft: Pi 5 + Bookworm

2. **Kernel-Updates:**
   - Kernel 6.6.42-v8-16k+ brach USB-C OTG Audio (Issue #6289)
   - HDMI-Audio kann nach Kernel-Update verschwinden

3. **Firmware-Updates:**
   - HDMI-Initialisierung ändert sich
   - EDID-Handling ändert sich

**Quellen:**
- Raspberry Pi Forums: "HDMI sound lost after update and reboot" (Thread #369555)
- LibreELEC Forum: "RPi5 HDMI Audio Stopped working" (Thread #30233)

### 2.2 Display-Manager-Wechsel (X11 ↔ Wayland)

**Problem:**
- **Wayland:** HDMI-Hotplug funktioniert, Audio bleibt verfügbar
- **X11:** Kein Hotplug, HDMI-A-1 wird deaktiviert
- X11-Skripte (`~/.xprofile`) können HDMI-A-1 explizit deaktivieren

**Quellen:**
- Raspberry Pi Forums: "No HDMI hotplug when switched to X11 - RPi5" (Thread #368781)
- Betrifft: Pi 5 mit X11 statt Wayland

**Lösung:**
- X11-Skripte reparieren: `./scripts/fix-x11-hdmi-a1-deactivation.sh`
- Oder zurück zu Wayland wechseln

### 2.3 vc4-kms-v3d Overlay deaktiviert

**Problem:**
- Wenn `dtoverlay=vc4-kms-v3d` deaktiviert ist → keine HDMI-Audio-Geräte
- ALSA zeigt "no soundcards found"
- PipeWire zeigt nur "Dummy Output"

**Quellen:**
- GitHub: raspberrypi/firmware #1871
- Betrifft: Pi 5 mit separaten Framebuffern

**Lösung:**
- `dtoverlay=vc4-kms-v3d` aktivieren (aber klont Displays)
- Oder HDMI-Audio akzeptieren, dass es nicht funktioniert

---

## 3. Freenove-spezifische Probleme

### 3.1 Mediaboard extrahiert Audio nur ohne Monitor

**Befund:**
- Viele Freenove Mediaboards extrahieren Audio nur, wenn kein Monitor angeschlossen ist
- Mit Monitor: Audio geht nur zum Monitor
- Ohne Monitor: Audio wird zu Gehäuselautsprechern extrahiert

**Mögliche Ursache:**
- Hardware-Limitierung des Mediaboards
- HDMI-Audio-Routing ändert sich je nach Monitor-Status

### 3.2 PCIe-Verbindung

**Befund:**
- Mediaboard ist über PCIe angeschlossen (FPC-Kabel)
- Erscheint **nicht** als separates PCIe-Audio-Gerät
- Extrahiert Audio **passiv** aus HDMI

**Quellen:**
- Freenove Dokumentation: FNK0107 Assembly Guide
- Betrifft: Alle Freenove Computer Case Kit Pro

### 3.3 EDID-Problem

**Problem:**
- Mediaboard präsentiert möglicherweise kein EDID
- Pi 5 erkennt HDMI-A-1 nicht als Audio-Gerät
- Lösung: EDID erzwingen (siehe unten)

---

## 4. Lösungsansätze (nach Wahrscheinlichkeit)

### 4.1 EDID erzwingen (Wahrscheinlichste Lösung)

**Problem:** Pi 5 erkennt HDMI-Audio nur mit EDID.

**Lösung:**
```bash
# EDID von HDMI-A-2 dumpen und für HDMI-A-1 erzwingen:
sudo ./scripts/fix-freenove-audio-edid.sh
sudo reboot
```

**Nach Neustart:**
```bash
# Aktiviere HDMI-A-1 Sink:
./scripts/activate-hdmi-a1-sink.sh

# Teste Audio:
./scripts/test-freenove-speakers-simple.sh
```

**Quellen:**
- Raspberry Pi Forums: "RasPi5 audio without EDID? [SOLVED]" (Thread #363732)
- Lösung: EDID dumpen und in `config.txt` erzwingen

### 4.2 X11-Skripte reparieren

**Problem:** X11-Skripte deaktivieren HDMI-A-1 automatisch.

**Lösung:**
```bash
# Repariere X11-Skripte:
./scripts/fix-x11-hdmi-a1-deactivation.sh

# Neu anmelden oder Neustart
```

**Quellen:**
- Eigene Diagnose: `~/.xprofile` und andere X11-Skripte enthalten `xrandr --output HDMI-1-1 --off`

### 4.3 Teste ohne Monitor

**Problem:** Mediaboard extrahiert Audio nur ohne Monitor.

**Lösung:**
```bash
# Monitor abstecken
# Dann testen:
./scripts/test-freenove-speakers-simple.sh
```

**Quellen:**
- Freenove-Dokumentation: Viele Mediaboards funktionieren nur ohne Monitor
- Eigene Erfahrung: Hardware-Limitierung

### 4.4 WirePlumber-Konfiguration zurücksetzen

**Problem:** Benutzerdefinierte WirePlumber-Konfiguration blockiert Audio.

**Lösung:**
```bash
# Setze WirePlumber-Konfiguration zurück:
./scripts/reset-wireplumber-audio-config.sh

# WirePlumber neu starten:
systemctl --user restart wireplumber.service
```

**Quellen:**
- Eigene Diagnose: Persistente WirePlumber-Konfigurationen können Audio blockieren

### 4.5 Vollständiger Power-Cycle

**Problem:** Nach Updates bleibt HDMI-Audio aus.

**Lösung:**
```bash
# Vollständiger Power-Cycle (nicht nur reboot):
sudo shutdown -h now
# Warte 10 Sekunden
# Dann wieder einschalten
```

**Quellen:**
- Raspberry Pi Forums: "HDMI sound lost after update and reboot" (Thread #369555)
- Einige Benutzer berichten, dass Power-Cycle hilft, reboot nicht

### 4.6 vc4-kms-v3d aktivieren

**Problem:** HDMI-Audio-Geräte fehlen komplett.

**Lösung:**
```bash
# Prüfe config.txt:
cat /boot/firmware/config.txt | grep vc4-kms

# Falls nicht aktiviert, füge hinzu:
# dtoverlay=vc4-kms-v3d
```

**Warnung:** Aktiviert vc4-kms klont Displays (keine separaten Framebuffer).

**Quellen:**
- GitHub: raspberrypi/firmware #1871
- Betrifft: Pi 5 mit separaten Framebuffern

---

## 5. Bekannte GitHub-Issues

### 5.1 Firmware Issue #1871
**Titel:** "RPi 5 - HDMI audio output not working with separate HDMI"
- **Status:** Offen (seit 2024-02-19)
- **Problem:** HDMI-Audio fehlt wenn vc4-kms-v3d deaktiviert ist
- **Link:** https://github.com/raspberrypi/firmware/issues/1871

### 5.2 Linux Issue #5525
**Titel:** "No HDMI audio with KMS"
- **Status:** Offen (seit 2023-06-28)
- **Problem:** Mit KMS fehlt HDMI-ALSA-Gerät
- **Link:** https://github.com/raspberrypi/linux/issues/5525

### 5.3 Linux Issue #5950
**Titel:** "No HDMI audio in Google Meet via Pipewire/PulseAudio on Bookworm"
- **Status:** Offen
- **Problem:** PipeWire zeigt nur "Dummy Output"
- **Link:** https://github.com/raspberrypi/linux/issues/5950

### 5.4 Linux Issue #6651
**Titel:** "Pi 5 HDMI/audio complaints"
- **Status:** Offen
- **Problem:** Sammel-Thread für Pi 5 HDMI-Audio-Probleme
- **Link:** https://github.com/raspberrypi/linux/issues/6651

---

## 6. Empfohlene Lösungsschritte (Priorität)

### Schritt 1: EDID erzwingen
```bash
sudo ./scripts/fix-freenove-audio-final.sh
sudo reboot
```

### Schritt 2: Nach Neustart - HDMI-A-1 Sink aktivieren
```bash
./scripts/activate-hdmi-a1-sink.sh
```

### Schritt 3: Audio testen
```bash
./scripts/test-freenove-speakers-simple.sh
```

### Schritt 4: Falls immer noch kein Ton - Teste ohne Monitor
```bash
# Monitor abstecken
./scripts/test-freenove-speakers-simple.sh
```

### Schritt 5: Falls immer noch kein Ton - Hardware prüfen
- FPC-Kabel zwischen Pi 5 und Mediaboard
- Lautsprecher-Verbindungen am Mediaboard
- Falls Gehäuse MUTE-Schalter hat: prüfen (nicht bei allen vorhanden)
- Power Supply (5V/5A empfohlen)

---

## 7. Warum Version 1.2.x.x funktionierte

**Mögliche Gründe:**

1. **Ältere PipeWire/WirePlumber-Version:**
   - Ältere Versionen hatten weniger Probleme mit HDMI-Audio
   - Nach Update: Regression eingeführt

2. **Ältere Kernel-Version:**
   - Kernel-Updates änderten HDMI-Audio-Verhalten
   - vc4hdmi-Treiber-Verhalten änderte sich

3. **Keine X11-Skripte:**
   - X11-Skripte wurden später hinzugefügt
   - Diese deaktivieren HDMI-A-1 automatisch

4. **Wayland statt X11:**
   - Wayland unterstützt HDMI-Hotplug besser
   - X11 deaktiviert HDMI-A-1 ohne Monitor

5. **Keine WirePlumber-Konfiguration:**
   - Benutzerdefinierte WirePlumber-Konfigurationen wurden später hinzugefügt
   - Diese können Audio blockieren

---

## 8. Zusammenfassung

**Hauptprobleme:**
1. ✅ **EDID-Problem:** Pi 5 erkennt HDMI-Audio nur mit EDID → Lösung: EDID erzwingen
2. ✅ **X11-Skripte:** Deaktivieren HDMI-A-1 automatisch → Lösung: Skripte reparieren
3. ✅ **WirePlumber:** Erstellt keine Sinks für HDMI-A-1 → Lösung: Profil aktivieren
4. ⚠️ **Mediaboard:** Extrahiert Audio möglicherweise nur ohne Monitor → Hardware-Limitierung
5. ⚠️ **System-Updates:** Brechen HDMI-Audio → Bekannte Regressionen

**Empfohlene Lösung:**
1. EDID erzwingen (`fix-freenove-audio-final.sh`)
2. Neustart
3. HDMI-A-1 Sink aktivieren (`activate-hdmi-a1-sink.sh`)
4. Audio testen
5. Falls kein Ton: Teste ohne Monitor

**Quellen:**
- Raspberry Pi Forums (mehrere Threads)
- GitHub Issues (raspberrypi/firmware, raspberrypi/linux)
- Freenove-Dokumentation
- Eigene Diagnose

---

## 9. Weitere Ressourcen

- **Raspberry Pi Forums:** https://forums.raspberrypi.com/
- **GitHub Issues:** https://github.com/raspberrypi/firmware/issues, https://github.com/raspberrypi/linux/issues
- **Freenove Support:** support@freenove.com
- **Freenove Dokumentation:** https://docs.freenove.com/projects/fnk0107/
