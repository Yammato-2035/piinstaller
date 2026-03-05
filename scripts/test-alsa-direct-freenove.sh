#!/bin/bash
# PI-Installer: Direkter ALSA-Test für Freenove Gehäuselautsprecher
#
# Testet beide HDMI-Karten direkt über ALSA (ohne PulseAudio),
# um zu prüfen, ob das Mediaboard Audio von einem bestimmten Port extrahiert.
#
# Ausführung: ./scripts/test-alsa-direct-freenove.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Direkter ALSA-Test für Freenove Gehäuselautsprecher ===${NC}"
echo ""

# Prüfe ob aplay verfügbar ist
if ! command -v aplay >/dev/null 2>&1; then
  echo -e "${RED}✗${NC} aplay nicht gefunden"
  exit 1
fi

# Liste alle verfügbaren ALSA-Karten
echo "Verfügbare ALSA-Karten:"
aplay -l 2>/dev/null | grep "^card" | while IFS= read -r line; do
  echo "  $line"
done
echo ""

# Teste jede Karte
for card in 0 1; do
  if ! aplay -l 2>/dev/null | grep -q "^card $card:"; then
    continue
  fi
  
  CARD_INFO=$(aplay -l 2>/dev/null | grep "^card $card:" | head -1)
  CARD_NAME=$(echo "$CARD_INFO" | sed 's/.*\[\([^]]*\)\].*/\1/' || echo "card$card")
  
  echo -e "${CYAN}[Test Card $card]${NC} $CARD_NAME"
  echo ""
  
  # Prüfe verfügbare Devices
  echo "  Verfügbare Devices:"
  aplay -l 2>/dev/null | grep "^card $card:" | while IFS= read -r line; do
    echo "    $line"
  done
  echo ""
  
  # Teste mit verschiedenen Device-Nummern
  for device in 0 1; do
    DEVICE_SPEC="hw:$card,$device"
    
    echo -e "  ${BLUE}→${NC} Teste Device: $DEVICE_SPEC"
    
    # Prüfe ob Device existiert
    if ! aplay -D "$DEVICE_SPEC" --dump-hw-params /dev/zero 2>&1 | grep -q "HW params"; then
      echo -e "    ${YELLOW}⚠${NC} Device nicht verfügbar"
      continue
    fi
    
    echo "    Device verfügbar, spiele Test-Ton..."
    
    # Generiere einen Test-Ton mit sox oder verwende speaker-test
    if command -v speaker-test >/dev/null 2>&1; then
      echo "    Verwende speaker-test..."
      timeout 3 speaker-test -c 2 -t sine -f 1000 -s 1 -D "$DEVICE_SPEC" 2>/dev/null &
      SPEAKER_PID=$!
      sleep 2
      kill $SPEAKER_PID 2>/dev/null || true
      wait $SPEAKER_PID 2>/dev/null || true
    elif command -v sox >/dev/null 2>&1; then
      echo "    Generiere Test-Ton mit sox..."
      sox -n -r 44100 -c 2 -t alsa "$DEVICE_SPEC" synth 1 sine 1000 2>/dev/null || true
    else
      echo -e "    ${YELLOW}⚠${NC} Kein Test-Ton-Tool gefunden (speaker-test/sox)"
      echo "    Installiere mit: sudo apt install alsa-utils sox"
      continue
    fi
    
    echo ""
    echo -e "    ${YELLOW}Kam der Ton aus den Gehäuselautsprechern?${NC}"
    echo -e "    ${CYAN}[j]${NC} Ja, dieser Device funktioniert!"
    echo -e "    ${CYAN}[n]${NC} Nein, nur HDMI-Monitor"
    echo -e "    ${CYAN}[s]${NC} Überspringen"
    echo ""
    read -p "    Deine Antwort (j/n/s): " answer
    
    case "$answer" in
      [jJ]*)
        echo -e "    ${GREEN}✓${NC} Dieser Device führt zu den Gehäuselautsprechern!"
        echo ""
        echo -e "${GREEN}=== Erfolgreich! ===${NC}"
        echo ""
        echo "Der richtige ALSA-Device für die Gehäuselautsprecher ist:"
        echo -e "  ${GREEN}$DEVICE_SPEC${NC}"
        echo ""
        echo "Du kannst diesen Device direkt verwenden mit:"
        echo "  aplay -D $DEVICE_SPEC <audio-file>"
        echo ""
        echo "Oder in PulseAudio/PipeWire als Standard-Sink setzen:"
        echo "  pactl set-default-sink alsa_output.platform-$(echo $CARD_INFO | grep -o 'platform-[0-9a-f]*' | head -1).hdmi.hdmi-stereo"
        echo ""
        exit 0
        ;;
      [nN]*)
        echo -e "    ${RED}✗${NC} Dieser Device führt nur zum HDMI-Monitor"
        ;;
      [sS]*)
        echo -e "    ${YELLOW}→${NC} Übersprungen"
        ;;
      *)
        echo -e "    ${YELLOW}→${NC} Übersprungen (ungültige Eingabe)"
        ;;
    esac
    
    echo ""
  done
  
  echo "---"
  echo ""
done

echo -e "${YELLOW}=== Kein passender Device gefunden ===${NC}"
echo ""
echo "Mögliche Lösungen:"
echo "  1. Prüfe, ob das Mediaboard richtig angeschlossen ist"
echo "  2. Prüfe, ob ein HDMI-Monitor angeschlossen ist (könnte das Routing beeinflussen)"
echo "  3. Prüfe die Freenove-Dokumentation für spezielle Konfiguration"
echo "  4. Versuche, den HDMI-Monitor abzustecken und erneut zu testen"
echo ""
