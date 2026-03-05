#!/bin/bash
# PI-Installer: Suspendierten HDMI-Sink aktivieren
#
# Aktiviert einen suspendierten HDMI-Sink und testet die Audio-Ausgabe.
#
# Ausführung: ./scripts/fix-suspended-hdmi-sink.sh [Sink-Name]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Suspendierten HDMI-Sink aktivieren ===${NC}"
echo ""

# Prüfe ob pactl verfügbar ist
PACTL=""
if command -v pactl >/dev/null 2>&1; then
  PACTL="pactl"
elif [ -f /usr/bin/pactl ]; then
  PACTL="/usr/bin/pactl"
fi

if [ -z "$PACTL" ]; then
  echo -e "${RED}✗${NC} pactl nicht gefunden"
  exit 1
fi

# Wenn Sink als Argument übergeben wurde, verwende diesen
if [ -n "$1" ]; then
  SINK_NAME="$1"
else
  # Finde suspendierten HDMI-Sink
  SINK_NAME=$(pactl list sinks short 2>/dev/null | grep -i "hdmi.*SUSPENDED" | head -1 | awk '{print $2}' || echo "")
  
  if [ -z "$SINK_NAME" ]; then
    # Fallback: Verwende Standard-Sink
    SINK_NAME=$(pactl get-default-sink 2>/dev/null || echo "")
  fi
fi

if [ -z "$SINK_NAME" ]; then
  echo -e "${RED}✗${NC} Kein Sink gefunden"
  exit 1
fi

echo -e "${CYAN}Sink:${NC} $SINK_NAME"
echo ""

# Prüfe Status
SINK_STATUS=$(pactl list sinks short 2>/dev/null | grep "$SINK_NAME" | awk '{print $NF}' || echo "")
echo "Status: $SINK_STATUS"
echo ""

if [ "$SINK_STATUS" = "SUSPENDED" ]; then
  echo -e "${YELLOW}⚠${NC} Sink ist suspendiert"
  echo ""
  echo "Aktiviere Sink..."
  
  # Setze als Standard-Sink (aktiviert ihn)
  pactl set-default-sink "$SINK_NAME" 2>/dev/null || {
    echo -e "${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
    exit 1
  }
  
  # Warte kurz
  sleep 1
  
  # Prüfe Status erneut
  NEW_STATUS=$(pactl list sinks short 2>/dev/null | grep "$SINK_NAME" | awk '{print $NF}' || echo "")
  echo "Neuer Status: $NEW_STATUS"
  echo ""
fi

# Prüfe Lautstärke
VOLUME=$(pactl get-sink-volume "$SINK_NAME" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
echo "Lautstärke: $VOLUME%"

if [ "$VOLUME" -lt 50 ]; then
  echo "Setze Lautstärke auf 70%..."
  pactl set-sink-volume "$SINK_NAME" 70% 2>/dev/null || true
fi

# Prüfe ob stumm geschaltet
MUTED=$(pactl get-sink-mute "$SINK_NAME" 2>/dev/null | awk '{print $2}' || echo "no")
echo "Stumm: $MUTED"

if [ "$MUTED" = "yes" ]; then
  echo "Entstumme..."
  pactl set-sink-mute "$SINK_NAME" 0 2>/dev/null || true
fi

echo ""
echo -e "${BLUE}→${NC} Spiele Test-Ton ab..."

if command -v paplay >/dev/null 2>&1; then
  TEST_FILE=""
  for test in /usr/share/sounds/freedesktop/stereo/bell.oga \
              /usr/share/sounds/alsa/Front_Left.wav \
              /usr/share/sounds/alsa/Front_Right.wav \
              /usr/share/sounds/alsa/Noise.wav; do
    if [ -f "$test" ]; then
      TEST_FILE="$test"
      break
    fi
  done
  
  if [ -n "$TEST_FILE" ]; then
    paplay --device="$SINK_NAME" "$TEST_FILE" 2>&1 &
    PA_PID=$!
    sleep 2
    kill $PA_PID 2>/dev/null || true
    echo ""
    echo -e "${GREEN}✓${NC} Test-Ton abgespielt"
  else
    echo -e "${YELLOW}⚠${NC} Keine Test-Datei gefunden"
  fi
else
  echo -e "${YELLOW}⚠${NC} paplay nicht gefunden"
fi

echo ""
echo -e "${CYAN}Prüfe Sink-Status:${NC}"
pactl list sinks short 2>/dev/null | grep "$SINK_NAME" | while IFS= read -r line; do
  echo "  $line"
done

echo ""
echo -e "${GREEN}Fertig.${NC}"
