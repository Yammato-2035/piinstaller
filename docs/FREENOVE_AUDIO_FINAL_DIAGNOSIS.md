# Finale Audio-Diagnose: Mediaboard extrahiert kein Audio

## Status

**Problem:** Audio geht nur zum HDMI-Monitor, nicht zu den Gehäuselautsprechern.

**Bisherige Tests:**
- ✅ Beide HDMI-Sinks sind verfügbar
- ✅ WirePlumber-Konfiguration zurückgesetzt
- ✅ Card 0 ist aktiv und wird von PipeWire verwendet
- ❌ Audio kommt nur aus HDMI-Monitor
- ❌ Kein Audio aus Gehäuselautsprechern

## Wichtige Erkenntnisse

1. **Card 0 ist belegt:** PipeWire verwendet Card 0, daher kann ALSA nicht direkt darauf zugreifen
2. **HDMI-A-1 ist disabled:** Display ist "disabled", aber Card 0 existiert trotzdem
3. **cmdline.txt enthält:** `video=HDMI-A-1:e` (sollte HDMI-A-1 aktivieren)
4. **Kernel aktiviert HDMI-A-1:** `[drm] forcing HDMI-A-1 connector on` - aber Display-Manager deaktiviert es wieder
5. **Keine ALSA-Mixer-Controls:** Card 0 und Card 1 haben keine Master/PCM-Controls

**WICHTIGER BEFUND:** Der Kernel aktiviert HDMI-A-1 beim Boot (`[drm] forcing HDMI-A-1 connector on`), aber der Display-Manager (X11 oder Wayland) deaktiviert es wieder. Siehe `docs/HDMI_A1_WAYFIRE_PROBLEM.md`.

## Mögliche Ursachen

### 1. Mediaboard extrahiert nur ohne Monitor (Wahrscheinlichste Ursache)

Das Mediaboard könnte so konfiguriert sein, dass es Audio nur extrahiert, wenn kein Monitor angeschlossen ist.

**Test:**
```bash
# Monitor abstecken
# Dann testen:
./scripts/test-audio-without-monitor.sh
```

### 2. Mediaboard benötigt spezielle HDMI-Konfiguration

Das Mediaboard könnte eine spezielle HDMI-Konfiguration benötigen, die nicht automatisch erkannt wird.

**Mögliche Lösungen:**

1. **Prüfe ob HDMI-A-1 aktiviert werden muss:**
   ```bash
   # HDMI-A-1 ist "disabled" - aktiviere es:
   ./scripts/activate-hdmi-a1-display.sh
   
   # Oder manuell:
   echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled
   systemctl --user restart wireplumber.service
   ```

2. **Prüfe ob beide HDMI-Ports gleichzeitig aktiv sein müssen:**
   ```bash
   # Aktiviere beide HDMI-Ports:
   echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled
   echo on | sudo tee /sys/class/drm/card2-HDMI-A-2/enabled
   ```

### 3. Mediaboard benötigt spezielle ALSA-Konfiguration

Das Mediaboard könnte eine spezielle ALSA-Konfiguration benötigen.

**Prüfe:**
```bash
# Prüfe ALSA-Konfiguration:
cat /etc/asound.conf 2>/dev/null || echo "Keine /etc/asound.conf"
cat ~/.asoundrc 2>/dev/null || echo "Keine ~/.asoundrc"
```

### 4. Wayland-spezifische Einstellungen

Wayland könnte Audio-Routing-Einstellungen haben, die das Mediaboard blockieren.

**Prüfe:**
```bash
# Prüfe Wayland-Konfiguration:
cat ~/.config/wayfire.ini 2>/dev/null | grep -i audio || echo "Keine Wayland-Audio-Einstellungen"
```

### 5. Hardware-Problem

Falls alle Software-Lösungen fehlschlagen, könnte es ein Hardware-Problem sein.

**Prüfe:**
- FPC-Kabel zwischen Pi 5 und Mediaboard
- Lautsprecher-Verbindungen am Mediaboard
- Falls Gehäuse MUTE-Schalter hat: prüfen
- Sichtbare Schäden am Mediaboard

## Komplette Reparatur

**WICHTIG:** X11-Skripte deaktivieren HDMI-A-1 automatisch! Repariere das zuerst:

```bash
# Repariere X11-Skripte, die HDMI-A-1 deaktivieren:
./scripts/fix-x11-hdmi-a1-deactivation.sh
```

Dieses Skript:
- Entfernt/kommentiert `xrandr --output HDMI-1-1 --off` aus `.xprofile`
- Repariert andere X11-Skripte
- Aktiviert HDMI-A-1 mit xrandr
- Startet WirePlumber neu

**Dann führe das komplette Reparatur-Skript aus:**

```bash
./scripts/fix-freenove-audio-complete.sh
```

## Nächste Schritte

### Schritt 1: Teste ohne Monitor

```bash
# Monitor abstecken
./scripts/test-audio-without-monitor.sh
```

### Schritt 2: Aktiviere HDMI-A-1 Display

```bash
# Versuche HDMI-A-1 Display zu aktivieren:
echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled

# Prüfe Status:
cat /sys/class/drm/card2-HDMI-A-1/enabled

# Teste Audio:
./scripts/test-both-hdmi-sinks.sh
```

### Schritt 3: Prüfe ALSA-Konfiguration

```bash
# Prüfe vorhandene ALSA-Konfigurationen:
cat /etc/asound.conf 2>/dev/null || echo "Keine /etc/asound.conf"
cat ~/.asoundrc 2>/dev/null || echo "Keine ~/.asoundrc"

# Prüfe ALSA-Karten:
cat /proc/asound/cards
aplay -l
```

### Schritt 4: Kontaktiere Freenove Support

Falls alle Lösungen fehlschlagen:

- **Freenove Support:** https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi
- **Email:** support@freenove.com
- **Website:** https://www.freenove.com

## Dokumentation

Siehe auch:
- `docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md` – Vollständige Problem-Analyse
- `docs/FREENOVE_AUDIO_TROUBLESHOOTING.md` – Allgemeine Troubleshooting-Dokumentation
- `docs/FREENOVE_COMPUTER_CASE.md` – Hardware-Zusammenbau (FPC-Kabel)
