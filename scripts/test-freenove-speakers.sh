#!/bin/bash
# PI-Installer: Freenove Gehäuselautsprecher testen
#
# Testet beide HDMI-Ports und prüft, welcher zu den Gehäuselautsprechern führt.
# Das Freenove Mediaboard extrahiert Audio aus HDMI, aber nur von einem Port.
#
# Ausführung: ./scripts/test-freenove-speakers.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove Gehäuselautsprecher testen ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${RED}✗${NC} Nicht auf Raspberry Pi"
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

# Hole alle verfügbaren HDMI-Sinks
HDMI_SINKS=$($PACTL list short sinks 2>/dev/null | grep -i "hdmi" || echo "")

if [ -z "$HDMI_SINKS" ]; then
  echo -e "${RED}✗${NC} Keine HDMI-Audio-Sinks gefunden"
  exit 1
fi

echo "Gefundene HDMI-Audio-Sinks:"
echo "$HDMI_SINKS" | while IFS= read -r line; do
  SINK_NAME=$(echo "$line" | awk '{print $2}')
  SINK_STATE=$(echo "$line" | awk '{print $NF}')
  echo "  - $SINK_NAME ($SINK_STATE)"
done
echo ""

# Speichere aktuellen Standard-Sink
CURRENT_SINK=$($PACTL get-default-sink 2>/dev/null || echo "")
echo -e "${CYAN}Aktueller Standard-Sink:${NC} ${CURRENT_SINK:-keiner}"
echo ""

# Teste jeden HDMI-Sink
echo -e "${CYAN}=== Teste jeden HDMI-Sink ===${NC}"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Bitte prüfe, ob der Ton aus den ${BLUE}Gehäuselautsprechern${NC} kommt,"
echo "         nicht aus einem HDMI-Monitor!"
echo ""

SINK_COUNT=0
SUCCESSFUL_SINK=""

while IFS= read -r line; do
  SINK_NAME=$(echo "$line" | awk '{print $2}')
  SINK_NUM=$(echo "$line" | awk '{print $1}')
  
  if [ -z "$SINK_NAME" ]; then
    continue
  fi
  
  SINK_COUNT=$((SINK_COUNT + 1))
  
  echo -e "${CYAN}[Test $SINK_COUNT]${NC} $SINK_NAME"
  echo ""
  
  # Setze als Standard-Sink
  echo "  Setze als Standard-Sink..."
  $PACTL set-default-sink "$SINK_NAME" 2>/dev/null || {
    echo -e "  ${RED}✗${NC} Fehler beim Setzen des Sinks"
    continue
  }
  
  # Warte kurz
  sleep 1
  
  # Prüfe Lautstärke und stelle sicher, dass nicht stumm geschaltet ist
  echo "  Prüfe Lautstärke..."
  VOLUME=$($PACTL get-sink-volume "$SINK_NAME" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
  if [ "$VOLUME" -lt 50 ]; then
    echo "  Setze Lautstärke auf 70%..."
    $PACTL set-sink-volume "$SINK_NAME" 70% 2>/dev/null || true
  fi
  
  # Prüfe ob stumm geschaltet
  MUTED=$($PACTL get-sink-mute "$SINK_NAME" 2>/dev/null | awk '{print $2}' || echo "no")
  if [ "$MUTED" = "yes" ]; then
    echo "  Entstumme..."
    $PACTL set-sink-mute "$SINK_NAME" 0 2>/dev/null || true
  fi
  
  # Spiele Test-Ton ab
  echo -e "  ${BLUE}→${NC} Spiele Test-Ton ab..."
  
  # Verwende paplay mit einer Test-Datei oder generiere einen Test-Ton
  if command -v paplay >/dev/null 2>&1; then
    # Versuche eine Test-Datei zu finden
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
      paplay --device="$SINK_NAME" "$TEST_FILE" 2>/dev/null &
      PA_PID=$!
      sleep 2
      kill $PA_PID 2>/dev/null || true
    else
      # Generiere einen Test-Ton mit sox oder speaker-test
      if command -v speaker-test >/dev/null 2>&1; then
        echo "  Verwende speaker-test..."
        timeout 2 speaker-test -c 2 -t sine -f 1000 -s 1 -D "$SINK_NAME" 2>/dev/null || true
      elif command -v sox >/dev/null 2>&1; then
        echo "  Generiere Test-Ton mit sox..."
        sox -n -t pulseaudio "$SINK_NAME" synth 1 sine 1000 2>/dev/null || true
      else
        echo -e "  ${YELLOW}⚠${NC} Kein Test-Ton-Tool gefunden (paplay/speaker-test/sox)"
      fi
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
      SUCCESSFUL_SINK="$SINK_NAME"
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
  
done <<< "$HDMI_SINKS"

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
  echo "Um diesen Sink dauerhaft zu setzen, füge folgendes zu deiner"
  echo "PulseAudio-Konfiguration hinzu oder verwende:"
  echo ""
  echo "  pactl set-default-sink $SUCCESSFUL_SINK"
  echo ""
  echo "Oder in /etc/pulse/default.pa:"
  echo "  set-default-sink $SUCCESSFUL_SINK"
  echo ""
elif [ -n "$CURRENT_SINK" ]; then
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
  echo "Stelle ursprünglichen Standard-Sink wieder her:"
  echo "  $CURRENT_SINK"
  $PACTL set-default-sink "$CURRENT_SINK" 2>/dev/null || true
  echo ""
  echo -e "${YELLOW}Hinweis:${NC} Das Mediaboard könnte:"
  echo "  1. Eine spezielle Konfiguration benötigen"
  echo "  2. Nur funktionieren, wenn kein Monitor angeschlossen ist"
  echo "  3. Über ALSA direkt angesprochen werden müssen"
  echo ""
else
  echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
  echo ""
fi

echo -e "${GREEN}Fertig.${NC}"
