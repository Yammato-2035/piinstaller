#!/bin/bash
# PI-Installer: Prüfe ob HDMI-A-1 als Sink verfügbar ist
#
# Prüft, ob HDMI-A-1 (107c701400) als Audio-Sink verfügbar ist,
# auch wenn dort kein Monitor angeschlossen ist.
#
# Ausführung: ./scripts/check-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Prüfe HDMI-A-1 Sink ===${NC}"
echo ""

# Prüfe cmdline.txt
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

if [ -f "$CMDLINE_FILE" ]; then
  CMDLINE_CONTENT=$(cat "$CMDLINE_FILE")
  if echo "$CMDLINE_CONTENT" | grep -q "video=HDMI-A-1"; then
    echo -e "${GREEN}✓${NC} cmdline.txt enthält: video=HDMI-A-1"
    echo "$CMDLINE_CONTENT" | grep -o "video=HDMI-A-1[^ ]*" | while IFS= read -r line; do
      echo "  $line"
    done
  else
    echo -e "${YELLOW}⚠${NC} cmdline.txt enthält kein video=HDMI-A-1"
  fi
else
  echo -e "${YELLOW}⚠${NC} cmdline.txt nicht gefunden"
fi
echo ""

# Prüfe ALSA-Karten
echo -e "${CYAN}ALSA-Karten:${NC}"
aplay -l 2>/dev/null | grep "^card" | while IFS= read -r line; do
  echo "  $line"
done
echo ""

# Prüfe PulseAudio/PipeWire Sinks
echo -e "${CYAN}PulseAudio/PipeWire Sinks:${NC}"
if command -v pactl >/dev/null 2>&1; then
  ALL_SINKS=$(pactl list sinks short 2>/dev/null || echo "")
  if [ -n "$ALL_SINKS" ]; then
    echo "$ALL_SINKS" | while IFS= read -r line; do
      if echo "$line" | grep -q "107c701400"; then
        echo -e "  ${GREEN}✓${NC} $line (HDMI-A-1)"
      elif echo "$line" | grep -q "107c706400"; then
        echo -e "  ${BLUE}→${NC} $line (HDMI-A-2)"
      else
        echo "  $line"
      fi
    done
  else
    echo -e "  ${YELLOW}⚠${NC} Keine Sinks gefunden"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} pactl nicht gefunden"
fi
echo ""

# Prüfe ob HDMI-A-1 als Sink verfügbar ist
HDMI_A1_SINK="alsa_output.platform-107c701400.hdmi.hdmi-stereo"
if echo "$ALL_SINKS" | grep -q "$HDMI_A1_SINK"; then
  echo -e "${GREEN}✓${NC} HDMI-A-1 ist als Sink verfügbar!"
  echo ""
  echo "Du kannst jetzt testen mit:"
  echo "  ./scripts/test-both-hdmi-sinks.sh"
else
  echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist nicht als Sink verfügbar"
  echo ""
  echo "Mögliche Lösungen:"
  echo "  1. Neustart durchführen (falls cmdline.txt geändert wurde):"
  echo "     sudo reboot"
  echo ""
  echo "  2. WirePlumber neu starten:"
  echo "     systemctl --user restart wireplumber"
  echo ""
  echo "  3. Prüfe cmdline.txt:"
  echo "     cat /boot/firmware/cmdline.txt | grep video"
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
