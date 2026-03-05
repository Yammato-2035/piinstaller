#!/bin/bash
# PI-Installer: Audio auf Freenove-Gehäuselautsprecher umschalten
#
# Setzt den Standard-Audio-Ausgang auf HDMI-A-1 (Card 0), damit der Ton
# über das Mediaboard an die Gehäuselautsprecher geht.
#
# Ausführung: ./scripts/set-audio-to-case-speakers.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SINK_CASE="alsa_output.platform-107c701400.hdmi.hdmi-stereo"  # HDMI-A-1, Gehäuselautsprecher

echo -e "${CYAN}=== Audio auf Gehäuselautsprecher umschalten ===${NC}"
echo ""

# 1. Prüfen ob HDMI-A-1 Sink existiert
if ! pactl list short sinks 2>/dev/null | grep -q "$SINK_CASE"; then
  echo -e "  ${YELLOW}HDMI-A-1 Sink nicht gefunden – aktiviere Card 0...${NC}"
  if [ -f "$(dirname "$0")/activate-hdmi-a1-sink.sh" ]; then
    "$(dirname "$0")/activate-hdmi-a1-sink.sh"
    echo ""
  else
    echo -e "  ${RED}✗${NC} Sink $SINK_CASE nicht verfügbar."
    echo "  Führe aus: ./scripts/activate-hdmi-a1-sink.sh"
    exit 1
  fi
fi

# 2. Standard-Sink auf Gehäuselautsprecher setzen
if pactl set-default-sink "$SINK_CASE" 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} Standard-Ausgang: Gehäuselautsprecher (HDMI-A-1)"
else
  echo -e "  ${RED}✗${NC} Konnte Standard-Sink nicht setzen"
  exit 1
fi

# 3. Lautstärke und Stummschaltung
pactl set-sink-mute "$SINK_CASE" 0 2>/dev/null || true
pactl set-sink-volume "$SINK_CASE" 70% 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} Lautstärke 70 %, Stummschaltung aus"
echo ""
echo "Aktueller Ausgang: $(pactl get-default-sink 2>/dev/null || echo 'unbekannt')"
echo ""
echo -e "${GREEN}Fertig.${NC} Der Ton geht jetzt auf die Gehäuselautsprecher."
