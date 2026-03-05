#!/bin/bash
# PI-Installer: Dual Display X11 – verzögert anwenden
# Layout nach 30 s anwenden (Display-Manager braucht Zeit zum Initialisieren).
# PCManFM-Desktop wird bereits in .xprofile ~10 s nach Login neu gestartet.
# Wichtig: DSI-1 Rotation sollte bereits in config.txt (display_rotate=1) gesetzt sein,
# damit der Bildschirm schon vor dem Bootvorgang gedreht ist.

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME:-/home/gabrielglienke}/.Xauthority}"

apply_layout() {
  # HDMI-1-1 ausschalten (kein Bildschirm angeschlossen)
  xrandr --output HDMI-1-1 --off 2>/dev/null || true
  
  # Beide Ausgaben in einem atomaren Befehl setzen (verhindert Position-Überschreibung)
  # HDMI-1-2 bei 480x0 (rechts vom DSI), DSI-1 bei 0x1440 (links unten)
  # Wichtig: --primary auf HDMI-1-2, damit Desktop dort erscheint
  xrandr --fb 3920x2240 --output HDMI-1-2 --mode 3440x1440 --rate 60 --primary --pos 480x0 --output DSI-1 --mode 800x480 --rotate left --pos 0x1440 2>/dev/null || \
  xrandr --fb 3920x2240 --output HDMI-1-2 --auto --primary --pos 480x0 --output DSI-1 --mode 800x480 --rotate left --pos 0x1440 2>/dev/null || true
  
  # Desktop sicherstellen: PCManFM auf Primary (HDMI-1-2) neu starten
  if command -v pcmanfm >/dev/null 2>&1; then
    sleep 1
    killall pcmanfm 2>/dev/null || true
    sleep 1
    for profile in LXDE-pi default; do
      [ -d "${XDG_CONFIG_HOME:-$HOME/.config}/pcmanfm/$profile" ] && break
      profile="default"
    done
    # PCManFM auf Primary Display starten (HDMI-1-2)
    DISPLAY="${DISPLAY:-:0}" pcmanfm --desktop --profile "$profile" &
  fi
}

# Warte 30 s, dann Layout anwenden (Display-Manager braucht Zeit)
sleep 30
apply_layout
