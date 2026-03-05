#!/bin/bash
# PI-Installer: Freenove Standard-Sink konfigurieren
#
# Konfiguriert den Standard-Sink für Freenove-Gehäuse.
# Das Mediaboard extrahiert Audio aus HDMI, daher sollte der Standard-Sink
# verwendet werden (wie in Version 1.2.x.x), auch wenn es ein HDMI-Sink ist.
#
# Ausführung: ./scripts/configure-freenove-default-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove Standard-Sink konfigurieren ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${YELLOW}⚠${NC} Nicht auf Raspberry Pi"
  exit 1
fi

# Prüfe ob Freenove-Gehäuse erkannt wird
FREENOVE_DETECTED=false
for bus in 1 0 6 7; do
  if i2cget -y $bus 0x21 0xfd 2>/dev/null | grep -q .; then
    FREENOVE_DETECTED=true
    break
  fi
done

if [ "$FREENOVE_DETECTED" != true ]; then
  echo -e "${YELLOW}⚠${NC} Freenove-Gehäuse nicht erkannt"
  echo "  Fortsetzen trotzdem..."
  echo ""
fi

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

# Hole aktuellen Standard-Sink
CURRENT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}Aktueller Standard-Sink:${NC} ${CURRENT_SINK:-keiner}"
echo ""

# Liste alle verfügbaren Sinks
echo "Verfügbare Sinks:"
SINKS=$($PACTL list short sinks 2>/dev/null || echo "")
if [ -z "$SINKS" ]; then
  echo -e "  ${RED}✗${NC} Keine Sinks gefunden"
  exit 1
fi

echo "$SINKS" | while IFS= read -r line; do
  SINK_NAME=$(echo "$line" | awk '{print $2}')
  SINK_STATE=$(echo "$line" | awk '{print $NF}')
  if [ "$SINK_NAME" = "$CURRENT_SINK" ]; then
    echo -e "  ${GREEN}→${NC} $SINK_NAME ($SINK_STATE) [AKTUELL]"
  else
    echo "  - $SINK_NAME ($SINK_STATE)"
  fi
done
echo ""

# Für Freenove: Verwende den Standard-Sink (wie in Version 1.2.x.x)
# Das Mediaboard extrahiert Audio aus HDMI und leitet es an die Gehäuselautsprecher weiter
if [ "$FREENOVE_DETECTED" = true ]; then
  echo -e "${CYAN}Freenove-Gehäuse erkannt${NC}"
  echo ""
  echo "Das Mediaboard extrahiert Audio aus HDMI und leitet es automatisch"
  echo "an die Gehäuselautsprecher weiter."
  echo ""
  
  if [ -n "$CURRENT_SINK" ]; then
    echo -e "${GREEN}✓${NC} Standard-Sink ist bereits gesetzt: $CURRENT_SINK"
    echo ""
    echo "Dieser Sink wird verwendet (wie in Version 1.2.x.x)."
    echo "Das Mediaboard sollte Audio automatisch an die Gehäuselautsprecher weiterleiten."
    echo ""
    
    # Prüfe Lautstärke
    VOLUME=$($PACTL get-sink-volume "$CURRENT_SINK" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
    if [ "$VOLUME" -lt 50 ]; then
      echo "Lautstärke ist niedrig ($VOLUME%). Setze auf 70%..."
      $PACTL set-sink-volume "$CURRENT_SINK" 70% 2>/dev/null || true
    fi
    
    # Prüfe ob stumm geschaltet
    MUTED=$($PACTL get-sink-mute "$CURRENT_SINK" 2>/dev/null | awk '{print $2}' || echo "no")
    if [ "$MUTED" = "yes" ]; then
      echo "Entstumme..."
      $PACTL set-sink-mute "$CURRENT_SINK" 0 2>/dev/null || true
    fi
    
    echo ""
    echo -e "${GREEN}Konfiguration abgeschlossen.${NC}"
    echo ""
    echo "Wenn der Ton nicht aus den Gehäuselautsprechern kommt:"
    echo "  1. Falls Gehäuse einen MUTE-Schalter hat: prüfen (nicht bei allen vorhanden)"
    echo "  2. Prüfe die Lautsprecher-Verbindungen"
    echo "  3. Teste mit: paplay /usr/share/sounds/alsa/Front_Left.wav"
    echo ""
  else
    echo -e "${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
    echo ""
    echo "Setze den ersten verfügbaren Sink als Standard..."
    FIRST_SINK=$(echo "$SINKS" | head -1 | awk '{print $2}')
    if [ -n "$FIRST_SINK" ]; then
      $PACTL set-default-sink "$FIRST_SINK" 2>/dev/null || {
        echo -e "${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
        exit 1
      }
      echo -e "${GREEN}✓${NC} Standard-Sink gesetzt: $FIRST_SINK"
    else
      echo -e "${RED}✗${NC} Kein Sink gefunden"
      exit 1
    fi
  fi
else
  echo -e "${YELLOW}⚠${NC} Freenove-Gehäuse nicht erkannt"
  echo ""
  echo "Falls du ein Freenove-Gehäuse verwendest, stelle sicher, dass:"
  echo "  1. Das I2C-Expansion-Board richtig angeschlossen ist"
  echo "  2. I2C aktiviert ist (raspi-config → Interface Options → I2C)"
  echo ""
fi

echo -e "${GREEN}Fertig.${NC}"
