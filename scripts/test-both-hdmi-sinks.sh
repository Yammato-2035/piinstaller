#!/bin/bash
# PI-Installer: Beide HDMI-Sinks für Freenove testen
#
# Testet beide bekannten HDMI-Sinks (107c701400 und 107c706400),
# um herauszufinden, welcher zu den Gehäuselautsprechern führt.
#
# Ausführung: ./scripts/test-both-hdmi-sinks.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Beide HDMI-Sinks für Freenove testen ===${NC}"
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

# Beide bekannten HDMI-Sinks
HDMI_SINK_1="alsa_output.platform-107c701400.hdmi.hdmi-stereo"  # HDMI-A-1
HDMI_SINK_2="alsa_output.platform-107c706400.hdmi.hdmi-stereo"  # HDMI-A-2

# Speichere aktuellen Standard-Sink
CURRENT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}Aktueller Standard-Sink:${NC} ${CURRENT_SINK:-keiner}"
echo ""

# Teste jeden Sink
for sink_name in "$HDMI_SINK_1" "$HDMI_SINK_2"; do
  SINK_COUNT=$((SINK_COUNT + 1))
  
  # Prüfe ob Sink existiert
  if ! $PACTL list sinks short 2>/dev/null | grep -q "$sink_name"; then
    echo -e "${CYAN}[Test $SINK_COUNT]${NC} $sink_name"
    echo -e "  ${YELLOW}⚠${NC} Sink nicht gefunden, überspringe..."
    echo ""
    continue
  fi
  
  echo -e "${CYAN}[Test $SINK_COUNT]${NC} $sink_name"
  
  # Bestimme HDMI-Port
  if echo "$sink_name" | grep -q "107c701400"; then
    PORT_INFO="(HDMI-A-1)"
  elif echo "$sink_name" | grep -q "107c706400"; then
    PORT_INFO="(HDMI-A-2)"
  else
    PORT_INFO=""
  fi
  echo "  Port: $PORT_INFO"
  echo ""
  
  # Setze als Standard-Sink
  echo "  Setze als Standard-Sink..."
  $PACTL set-default-sink "$sink_name" 2>/dev/null || {
    echo -e "  ${RED}✗${NC} Fehler beim Setzen des Sinks"
    continue
  }
  
  # Warte kurz
  sleep 1
  
  # Prüfe Lautstärke
  echo "  Prüfe Lautstärke..."
  VOLUME=$($PACTL get-sink-volume "$sink_name" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
  if [ "$VOLUME" -lt 50 ]; then
    echo "  Setze Lautstärke auf 70%..."
    $PACTL set-sink-volume "$sink_name" 70% 2>/dev/null || true
  fi
  
  # Prüfe ob stumm geschaltet
  MUTED=$($PACTL get-sink-mute "$sink_name" 2>/dev/null | awk '{print $2}' || echo "no")
  if [ "$MUTED" = "yes" ]; then
    echo "  Entstumme..."
    $PACTL set-sink-mute "$sink_name" 0 2>/dev/null || true
  fi
  
  # Spiele Test-Ton ab
  echo -e "  ${BLUE}→${NC} Spiele Test-Ton ab..."
  
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
      paplay --device="$sink_name" "$TEST_FILE" 2>/dev/null &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
    else
      echo -e "  ${YELLOW}⚠${NC} Keine Test-Datei gefunden"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} paplay nicht gefunden"
  fi
  
  echo ""
  echo -e "  ${YELLOW}Kam der Ton aus den Gehäuselautsprechern?${NC}"
  echo -e "  ${CYAN}[j]${NC} Ja, dieser Sink funktioniert!"
  echo -e "  ${CYAN}[n]${NC} Nein, nur HDMI-Monitor"
  echo -e "  ${CYAN}[s]${NC} Überspringen"
  echo ""
  read -p "  Deine Antwort (j/n/s): " answer
  
  case "$answer" in
    [jJ]*)
      echo -e "  ${GREEN}✓${NC} Dieser Sink führt zu den Gehäuselautsprechern!"
      SUCCESSFUL_SINK="$sink_name"
      break
      ;;
    [nN]*)
      echo -e "  ${RED}✗${NC} Dieser Sink führt nur zum HDMI-Monitor"
      ;;
    [sS]*)
      echo -e "  ${YELLOW}→${NC} Übersprungen"
      ;;
    *)
      echo -e "  ${YELLOW}→${NC} Übersprungen (ungültige Eingabe)"
      ;;
  esac
  
  echo ""
  echo "---"
  echo ""
done

# Wiederherstelle ursprünglichen Standard-Sink oder setze den erfolgreichen
if [ -n "$SUCCESSFUL_SINK" ]; then
  echo -e "${GREEN}=== Erfolgreich! ===${NC}"
  echo ""
  echo "Der richtige Sink für die Gehäuselautsprecher ist:"
  echo -e "  ${GREEN}$SUCCESSFUL_SINK${NC}"
  echo ""
  echo "Setze als Standard-Sink..."
  $PACTL set-default-sink "$SUCCESSFUL_SINK" 2>/dev/null || true
  echo ""
  echo "Um diesen Sink dauerhaft zu setzen:"
  echo "  pactl set-default-sink $SUCCESSFUL_SINK"
  echo ""
  echo "Oder in WirePlumber-Konfiguration:"
  echo "  wpctl set-default <ID>"
  echo ""
elif [ -n "$CURRENT_SINK" ]; then
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
  echo "Stelle ursprünglichen Standard-Sink wieder her:"
  echo "  $CURRENT_SINK"
  $PACTL set-default-sink "$CURRENT_SINK" 2>/dev/null || true
  echo ""
else
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
fi

echo -e "${GREEN}Fertig.${NC}"
