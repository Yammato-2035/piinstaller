#!/bin/bash
# PI-Installer: Setze nach Login den Standard-Sink auf HDMI-A-1 (Gehäuselautsprecher)
#
# Problem: Nach Neustart setzt WirePlumber den Standard-Sink auf HDMI-A-2 (Monitor),
# weil HDMI-A-1 als "nicht verfügbar" gilt (kein Monitor angeschlossen – DSP1 hängt intern).
# Lösung: Dieses Skript wird per Autostart mit Verzögerung ausgeführt und setzt
# den Standard-Sink mehrfach auf HDMI-A-1, damit der Ton an Gehäuselautsprechern
# und Kopfhörerbuchse ankommt (überholt späte WirePlumber-Auswahl).
#
# Einmalig einrichten: ./scripts/install-freenove-default-sink-autostart.sh
# Zusätzlich: ./scripts/configure-wireplumber-hdmi-a1.sh (Priorität für HDMI-A-1)

set -e

SINK_CASE="alsa_output.platform-107c701400.hdmi.hdmi-stereo"
DELAY="${1:-6}"

# Verzögerung, damit WirePlumber/PipeWire die Sinks angelegt hat
sleep "$DELAY"

if ! command -v pactl >/dev/null 2>&1; then
  exit 0
fi

set_default_if_present() {
  if pactl list short sinks 2>/dev/null | grep -q "$SINK_CASE"; then
    pactl set-default-sink "$SINK_CASE" 2>/dev/null || true
    pactl set-sink-mute "$SINK_CASE" 0 2>/dev/null || true
    pactl set-sink-volume "$SINK_CASE" 70% 2>/dev/null || true
  fi
}

# Sofort setzen
set_default_if_present

# Nochmals nach 8 s (falls WirePlumber den Default später gesetzt hat)
sleep 8
set_default_if_present

# Ein drittes Mal nach weiteren 12 s
sleep 12
set_default_if_present
