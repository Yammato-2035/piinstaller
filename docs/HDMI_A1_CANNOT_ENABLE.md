# Problem: HDMI-A-1 kann nicht aktiviert werden

## Befund

**HDMI-A-1 kann nicht aktiviert werden**, auch nicht mit sudo:
- ❌ `echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled` → "Keine Berechtigung"
- ❌ `sudo bash -c 'echo on > /sys/class/drm/card2-HDMI-A-1/enabled'` → "Keine Berechtigung"
- ✅ `cmdline.txt` enthält `video=HDMI-A-1:e`
- ✅ Kernel-Logs zeigen: `[drm] forcing HDMI-A-1 connector on`
- ❌ HDMI-A-1 bleibt trotzdem "disabled"

## Ursache

**Der Kernel aktiviert HDMI-A-1 beim Boot**, aber ein Prozess (wahrscheinlich der Display-Manager oder DRM-Treiber) deaktiviert es wieder oder verhindert die Aktivierung.

Mögliche Gründe:
1. **Display-Manager (X11/Wayland) deaktiviert HDMI-A-1** automatisch, wenn kein Monitor erkannt wird
2. **DRM-Treiber verhindert Aktivierung** von HDMI-Ports ohne angeschlossenen Monitor
3. **Datei ist schreibgeschützt** oder von einem Prozess gesperrt

## Lösungen

### Lösung 1: System-Neustart (Empfohlen)

Da `cmdline.txt` bereits `video=HDMI-A-1:e` enthält, sollte ein Neustart HDMI-A-1 aktivieren:

```bash
sudo reboot
```

Nach dem Neustart sollte HDMI-A-1 automatisch aktiviert sein.

### Lösung 2: X11-Skripte reparieren

Die `.xprofile` wurde bereits repariert, aber möglicherweise gibt es andere Skripte:

```bash
# Repariere alle X11-Skripte:
./scripts/fix-x11-hdmi-a1-deactivation.sh

# Prüfe ob andere Skripte HDMI-A-1 deaktivieren:
grep -r "xrandr.*HDMI.*--off" ~/.xprofile ~/.xinitrc ~/.xsessionrc 2>/dev/null
```

### Lösung 3: Wayfire-Konfiguration anpassen (Wenn unter Wayland)

Falls unter Wayland:

```bash
# Bearbeite wayfire.ini:
nano ~/.config/wayfire.ini

# Füge hinzu:
[output:HDMI-A-1]
mode = auto
enabled = true
```

### Lösung 4: Kernel-Parameter prüfen

Prüfe ob `cmdline.txt` korrekt geladen wird:

```bash
# Prüfe Kernel-Command-Line:
cat /proc/cmdline | grep -o "video=HDMI-A-1[^ ]*"

# Falls nicht vorhanden, füge hinzu:
sudo nano /boot/firmware/cmdline.txt
# Füge hinzu: video=HDMI-A-1:e
```

### Lösung 5: DRM-Kernel-Modul neu laden (Experimentell)

**VORSICHT:** Dies könnte den Display-Manager zum Absturz bringen!

```bash
# Nur wenn nichts anderes funktioniert:
sudo modprobe -r vc4
sudo modprobe vc4
```

## Überwachung

Um herauszufinden, welcher Prozess HDMI-A-1 deaktiviert:

```bash
# Überwache Änderungen:
./scripts/monitor-hdmi-a1-changes.sh
```

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_FINAL_DIAGNOSIS.md` – Finale Diagnose
- `docs/HDMI_A1_WAYFIRE_PROBLEM.md` – Display-Manager Problem
- `docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md` – Problem-Analyse
