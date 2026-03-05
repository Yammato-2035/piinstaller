#!/bin/bash
# PI-Installer: Aktiviere alle HDMI-Sinks
#
# Beide HDMI-Sinks sind SUSPENDED. Dieses Skript aktiviert sie.
#
# Ausführung: ./scripts/activate-hdmi-sinks.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Aktiviere HDMI-Sinks ===${NC}"
echo ""

# Finde alle HDMI-Sinks
HDMI_SINKS=$(pactl list short sinks 2>/dev/null | grep "hdmi" | awk '{print $2}' || echo "")

if [ -z "$HDMI_SINKS" ]; then
  echo -e "${RED}✗${NC} Keine HDMI-Sinks gefunden"
  exit 1
fi

echo -e "${CYAN}[1] Gefundene HDMI-Sinks:${NC}"
echo "$HDMI_SINKS" | while read -r sink; do
  STATE=$(pactl list sinks short 2>/dev/null | grep "$sink" | awk '{print $NF}' || echo "unknown")
  echo "  - $sink (Status: $STATE)"
done
echo ""

echo -e "${CYAN}[2] Aktiviere HDMI-Sinks:${NC}"
echo "$HDMI_SINKS" | while read -r sink; do
  echo "  Aktiviere $sink..."
  
  # Setze als Standard-Sink (aktiviert ihn)
  if pactl set-default-sink "$sink" 2>/dev/null; then
    echo -e "    ${GREEN}✓${NC} Als Standard-Sink gesetzt"
  else
    echo -e "    ${YELLOW}⚠${NC} Konnte nicht als Standard-Sink setzen"
  fi
  
  # Aktiviere Sink (falls SUSPENDED)
  if pactl set-sink-mute "$sink" 0 2>/dev/null; then
    echo -e "    ${GREEN}✓${NC} Stummschaltung aufgehoben"
  fi
  
  # Setze Lautstärke
  if pactl set-sink-volume "$sink" 70% 2>/dev/null; then
    echo -e "    ${GREEN}✓${NC} Lautstärke auf 70% gesetzt"
  fi
  
  # Versuche Sink zu aktivieren durch kurzes Abspielen
  # (SUSPENDED-Sinks werden aktiviert, wenn Audio gespielt wird)
  echo -e "    ${CYAN}→${NC} Versuche Sink zu aktivieren..."
  
  echo ""
done

echo -e "${CYAN}[3] Prüfe Status nach Aktivierung:${NC}"
sleep 1
pactl list sinks short 2>/dev/null | grep "hdmi" | while read -r line; do
  STATE=$(echo "$line" | awk '{print $NF}')
  SINK=$(echo "$line" | awk '{print $2}')
  if [ "$STATE" = "SUSPENDED" ]; then
    echo -e "  ${YELLOW}⚠${NC} $SINK ist immer noch SUSPENDED"
  else
    echo -e "  ${GREEN}✓${NC} $SINK ist aktiv ($STATE)"
  fi
done

echo ""
echo -e "${CYAN}[4] Aktueller Standard-Sink:${NC}"
DEFAULT_SINK=$(pactl get-default-sink 2>/dev/null || echo "keiner")
echo "  $DEFAULT_SINK"
echo ""

echo -e "${CYAN}[5] Nächste Schritte:${NC}"
echo ""
echo "1. Teste beide HDMI-Sinks:"
echo "   ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo "2. Falls Sinks immer noch SUSPENDED sind:"
echo "   - Starte Audio-Anwendung (z.B. Musik abspielen)"
echo "   - Oder spiele Test-Ton: paplay /usr/share/sounds/alsa/Front_Left.wav"
echo ""
echo "3. Prüfe ob Ton aus Gehäuselautsprechern kommt:"
echo "   - Teste mit verschiedenen Sinks"
echo "   - Falls Gehäuse MUTE-Schalter hat: prüfen"
echo ""
echo -e "${GREEN}Fertig.${NC}"
