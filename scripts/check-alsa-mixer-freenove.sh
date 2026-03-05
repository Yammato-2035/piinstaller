#!/bin/bash
# PI-Installer: ALSA-Mixer-Einstellungen für Freenove prüfen
#
# Prüft alle ALSA-Mixer-Einstellungen für beide HDMI-Karten,
# um zu sehen, ob es separate Kanäle für Lautsprecher/Kopfhörer gibt.
#
# Ausführung: ./scripts/check-alsa-mixer-freenove.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== ALSA-Mixer-Einstellungen für Freenove prüfen ===${NC}"
echo ""

# Prüfe ob amixer verfügbar ist
if ! command -v amixer >/dev/null 2>&1; then
  echo -e "${RED}✗${NC} amixer nicht gefunden"
  exit 1
fi

# Prüfe alle ALSA-Karten
for card in 0 1 2 3 4 5; do
  if [ ! -d "/proc/asound/card$card" ]; then
    continue
  fi
  
  CARD_NAME=$(cat /proc/asound/cards 2>/dev/null | grep "^[[:space:]]*$card" | sed 's/^[[:space:]]*[0-9]*[[:space:]]*\[\([^]]*\)\].*/\1/' || echo "card$card")
  
  echo -e "${CYAN}[Card $card]${NC} $CARD_NAME"
  echo ""
  
  # Liste alle verfügbaren Controls
  echo "  Verfügbare Controls:"
  amixer -c $card scontrols 2>/dev/null | head -20 | while IFS= read -r line; do
    echo "    $line"
  done
  echo ""
  
  # Zeige alle Werte
  echo "  Aktuelle Werte:"
  amixer -c $card sget Master 2>/dev/null | head -10 | while IFS= read -r line; do
    echo "    $line"
  done || echo -e "    ${YELLOW}⚠${NC} Kein Master-Control"
  
  # Prüfe nach Speaker/Headphone/PCM
  for control in Master PCM Speaker Headphone; do
    echo ""
    echo "  Control: $control"
    amixer -c $card sget "$control" 2>/dev/null | grep -E "Playback|Mono|Capabilities|Limits" | head -5 | while IFS= read -r line; do
      echo "    $line"
    done || echo -e "    ${YELLOW}⚠${NC} Nicht verfügbar"
  done
  
  echo ""
  echo "  Alle Controls mit Werten:"
  amixer -c $card 2>/dev/null | grep -E "^Simple mixer control|Playback|Mono|dB|\[on\]|\[off\]" | head -30 | while IFS= read -r line; do
    echo "    $line"
  done
  
  echo ""
  echo "---"
  echo ""
done

echo -e "${GREEN}Fertig.${NC}"
echo ""
echo -e "${YELLOW}Hinweis:${NC} Wenn es separate Speaker/Headphone-Controls gibt,"
echo "         könnten diese das Routing zwischen HDMI-Monitor"
echo "         und Gehäuselautsprechern steuern."
