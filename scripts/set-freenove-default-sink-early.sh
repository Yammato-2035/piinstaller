#!/bin/bash
# PI-Installer: HDMI-A-1 sehr früh aktivieren und als Standard-Sink setzen
#
# Wird vom systemd-User-Service direkt nach WirePlumber ausgeführt (nicht erst
# beim Desktop-Autostart). So ist HDMI-A-1 aktiv, bevor Anwendungen den
# Standard-Sink übernehmen (Monitor).
#
# Ausführung: durch freenove-default-sink.service (systemd --user)
# Manuell: ./scripts/set-freenove-default-sink-early.sh

SINK_CASE="alsa_output.platform-107c701400.hdmi.hdmi-stereo"
CARD_NAME="alsa_card.platform-107c701400.hdmi"

# Kurz warten, bis WirePlumber die Karten/Sinks angelegt hat
sleep 2

command -v pactl >/dev/null 2>&1 || exit 0

# Sink existiert noch nicht → Karten-Profil aktivieren (erzeugt Sink)
if ! pactl list short sinks 2>/dev/null | grep -q "$SINK_CASE"; then
  pactl set-card-profile "$CARD_NAME" output:hdmi-stereo 2>/dev/null || true
  sleep 1
fi

# Standard-Sink setzen
if pactl list short sinks 2>/dev/null | grep -q "$SINK_CASE"; then
  pactl set-default-sink "$SINK_CASE" 2>/dev/null || true
  pactl set-sink-mute "$SINK_CASE" 0 2>/dev/null || true
  pactl set-sink-volume "$SINK_CASE" 70% 2>/dev/null || true
fi
