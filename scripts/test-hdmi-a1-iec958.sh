#!/bin/bash
# PI-Installer: Teste HDMI-A-1 im IEC958-Modus (S/PDIF)
#
# HDMI-A-1 läuft im IEC958-Modus (S/PDIF), nicht im PCM-Modus.
# Das Mediaboard könnte digitales Audio (S/PDIF) extrahieren.
#
# Ausführung: ./scripts/test-hdmi-a1-iec958.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Teste HDMI-A-1 im IEC958-Modus (S/PDIF) ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${RED}✗${NC} Nicht auf Raspberry Pi"
  exit 1
fi

echo -e "${CYAN}Befund:${NC}"
echo "  HDMI-A-1 (Card 0) läuft im IEC958-Modus (S/PDIF)"
echo "  Das Mediaboard könnte digitales Audio (S/PDIF) extrahieren"
echo ""

# Prüfe verfügbare Formate
echo -e "${CYAN}Verfügbare Formate für Card 0 (HDMI-A-1):${NC}"
aplay -D hw:0,0 --dump-hw-params /dev/zero 2>&1 | grep -E "Available formats|IEC958" | head -10
echo ""

# Prüfe ALSA-Mixer
echo -e "${CYAN}ALSA-Mixer Controls für Card 0:${NC}"
amixer -c 0 scontrols 2>/dev/null | head -10
echo ""

# Prüfe IEC958-Status
echo -e "${CYAN}IEC958-Status:${NC}"
amixer -c 0 get IEC958 2>/dev/null | head -10 || echo "  Kein IEC958-Control gefunden"
echo ""

# Versuche über PipeWire/PulseAudio zu testen
echo -e "${CYAN}Teste über PipeWire/PulseAudio:${NC}"
if command -v pactl >/dev/null 2>&1; then
  # Prüfe ob Card 0 als Sink verfügbar ist (auch wenn nicht als HDMI-A-1 erkannt)
  ALL_SINKS=$(pactl list sinks 2>/dev/null || echo "")
  
  # Suche nach Sink mit Card 0
  CARD0_SINK=""
  if [ -n "$ALL_SINKS" ]; then
    CURRENT_SINK=""
    while IFS= read -r line; do
      if echo "$line" | grep -q "^Sink #"; then
        CURRENT_SINK=$(echo "$line" | awk '{print $2}' | tr -d '#')
      elif [ -n "$CURRENT_SINK" ] && echo "$line" | grep -q "alsa.card = \"0\""; then
        CARD0_SINK=$(pactl list sinks short 2>/dev/null | grep "^$CURRENT_SINK" | awk '{print $2}' || echo "")
        break
      fi
    done <<< "$ALL_SINKS"
  fi
  
  if [ -n "$CARD0_SINK" ]; then
    echo -e "${GREEN}✓${NC} Card 0 als Sink gefunden: $CARD0_SINK"
    echo ""
    echo "Setze als Standard-Sink..."
    pactl set-default-sink "$CARD0_SINK" 2>/dev/null || {
      echo -e "${RED}✗${NC} Fehler beim Setzen des Sinks"
      exit 1
    }
    
    # Warte kurz
    sleep 1
    
    # Prüfe Lautstärke
    VOLUME=$(pactl get-sink-volume "$CARD0_SINK" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
    if [ "$VOLUME" -lt 50 ]; then
      echo "Setze Lautstärke auf 70%..."
      pactl set-sink-volume "$CARD0_SINK" 70% 2>/dev/null || true
    fi
    
    # Prüfe ob stumm geschaltet
    MUTED=$(pactl get-sink-mute "$CARD0_SINK" 2>/dev/null | awk '{print $2}' || echo "no")
    if [ "$MUTED" = "yes" ]; then
      echo "Entstumme..."
      pactl set-sink-mute "$CARD0_SINK" 0 2>/dev/null || true
    fi
    
    # Spiele Test-Ton ab
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
        paplay --device="$CARD0_SINK" "$TEST_FILE" 2>/dev/null &
        PA_PID=$!
        sleep 2
        kill $PA_PID 2>/dev/null || true
      else
        echo -e "${YELLOW}⚠${NC} Keine Test-Datei gefunden"
      fi
    else
      echo -e "${YELLOW}⚠${NC} paplay nicht gefunden"
    fi
    
    echo ""
    echo -e "${YELLOW}Kam der Ton aus den Gehäuselautsprechern?${NC}"
    echo -e "${CYAN}[j]${NC} Ja, HDMI-A-1 funktioniert!"
    echo -e "${CYAN}[n]${NC} Nein, immer noch kein Ton"
    echo ""
    read -p "Deine Antwort (j/n): " answer
    
    case "$answer" in
      [jJ]*)
        echo -e "${GREEN}✓${NC} HDMI-A-1 führt zu den Gehäuselautsprechern!"
        echo ""
        echo "HDMI-A-1 ist jetzt als Standard-Sink gesetzt."
        echo "Der Ton sollte jetzt aus den Gehäuselautsprechern kommen."
        ;;
      [nN]*)
        echo -e "${RED}✗${NC} HDMI-A-1 funktioniert auch nicht"
        echo ""
        echo "Mögliche Ursachen:"
        echo "  1. Hardware-Problem (Lautsprecher-Verbindungen, Mediaboard)"
        echo "  2. Mediaboard funktioniert nur ohne angeschlossenen Monitor"
        echo "  3. Defektes Mediaboard"
        echo ""
        echo "Siehe: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md"
        ;;
      *)
        echo -e "${YELLOW}→${NC} Ungültige Eingabe"
        ;;
    esac
  else
    echo -e "${YELLOW}⚠${NC} Card 0 ist nicht als PipeWire-Sink verfügbar"
    echo ""
    echo "Mögliche Lösungen:"
    echo "  1. Neustart durchführen (falls cmdline.txt geändert wurde):"
    echo "     sudo reboot"
    echo ""
    echo "  2. WirePlumber-Konfiguration prüfen"
    echo ""
    echo "  3. Direkt über ALSA testen (mit IEC958-Format):"
    echo "     # Das Mediaboard könnte IEC958-Signale extrahieren"
  fi
else
  echo -e "${YELLOW}⚠${NC} pactl nicht gefunden"
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
