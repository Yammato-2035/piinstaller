# Problem: Display-Manager (X11/Wayland) deaktiviert HDMI-A-1 automatisch

## Befund

**HDMI-A-1 kann nicht aktiviert werden**, obwohl:
- ✅ `cmdline.txt` enthält `video=HDMI-A-1:e`
- ✅ Kernel-Logs zeigen: `[drm] forcing HDMI-A-1 connector on`
- ✅ Wayfire/X11-Konfiguration versucht HDMI-A-1 zu aktivieren
- ❌ HDMI-A-1 bleibt trotzdem "disabled"

**WICHTIG:** Der Kernel aktiviert HDMI-A-1 (`[drm] forcing HDMI-A-1 connector on`), aber ein Display-Manager (X11 oder Wayland) deaktiviert es wieder.

## Ursache

**Wayfire/Wayland könnte HDMI-A-1 automatisch deaktivieren**, wenn:
1. Kein Monitor angeschlossen ist
2. Wayfire erkennt HDMI-A-1 als "nicht verwendet"
3. Ein anderer Display-Manager setzt HDMI-A-1 auf "disabled"

## Wayfire-Konfiguration

Die `~/.config/wayfire.ini` enthält bereits einen Autostart-Befehl:

```ini
[autostart]
autostart_enable_hdmi = sh -c 'sleep 5 && wlr-randr --output HDMI-A-1 --on 2>/dev/null; wlr-randr --output HDMI-A-2 --on 2>/dev/null'
```

Dieser Befehl sollte HDMI-A-1 aktivieren, aber es funktioniert möglicherweise nicht.

## Lösungen

### Lösung 1: X11-Skripte prüfen (Wenn unter X11)

**WICHTIG:** Unter X11 könnte ein xrandr-Skript HDMI-A-1 deaktivieren:

```bash
# Aktiviere HDMI-A-1 unter X11:
./scripts/fix-hdmi-a1-x11.sh

# Oder manuell:
export DISPLAY=:0
xrandr --output HDMI-1-1 --auto
```

**Prüfe xrandr-Skripte:**
```bash
# Prüfe .xprofile, .xinitrc, etc.:
grep -r "xrandr.*HDMI.*off\|xrandr.*--off" ~/.xprofile ~/.xinitrc ~/.xsessionrc 2>/dev/null
```

### Lösung 2: Wayfire-Konfiguration anpassen (Wenn unter Wayland)

Erzwinge HDMI-A-1 in Wayfire-Konfiguration:

```bash
# Bearbeite wayfire.ini:
nano ~/.config/wayfire.ini

# Füge hinzu oder aktualisiere:
[output:HDMI-A-1]
mode = auto
enabled = true
position = 800,0

# Oder erzwinge es im Autostart:
[autostart]
autostart_force_hdmi_a1 = sh -c 'sleep 10 && wlr-randr --output HDMI-A-1 --on --mode 1920x1080 2>/dev/null || true'
```

### Lösung 2: Wayfire neu starten

```bash
# Wayfire neu starten (falls als Service):
systemctl --user restart wayfire.service

# Oder abmelden/anmelden
```

### Lösung 3: wlr-randr manuell ausführen

```bash
# Aktiviere HDMI-A-1 mit wlr-randr:
wlr-randr --output HDMI-A-1 --on

# Prüfe Status:
cat /sys/class/drm/card2-HDMI-A-1/enabled

# Falls das funktioniert, füge es zu wayfire.ini hinzu
```

### Lösung 4: System-Neustart

Da `cmdline.txt` bereits `video=HDMI-A-1:e` enthält, könnte ein Neustart helfen:

```bash
sudo reboot
```

Nach dem Neustart sollte HDMI-A-1 automatisch aktiviert sein.

## Überwachung

Um herauszufinden, welcher Prozess HDMI-A-1 deaktiviert:

```bash
# Überwache Änderungen an HDMI-A-1:
./scripts/monitor-hdmi-a1-changes.sh
```

Dieses Skript zeigt, wann und von welchem Prozess HDMI-A-1 auf "disabled" gesetzt wird.

## Dokumentation

Siehe auch:
- `docs/FREENOVE_AUDIO_FINAL_DIAGNOSIS.md` – Finale Diagnose
- `docs/HDMI_A1_SINK_PROBLEM.md` – Problem mit HDMI-A-1 Sink-Erstellung
- `scripts/setup-pi5-dual-display-dsi-hdmi0.sh` – Dual Display Setup
