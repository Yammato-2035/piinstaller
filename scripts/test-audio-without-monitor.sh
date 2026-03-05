#!/bin/bash
# PI-Installer: Audio-Test ohne Monitor (für SSH)
#
# Testet automatisch beide HDMI-Sinks, während der Monitor abgesteckt ist.
# Über SSH ausführbar - kein Monitor nötig.
#
# Ausführung: ./scripts/test-audio-without-monitor.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Audio-Test ohne Monitor (für SSH) ===${NC}"
echo ""
echo "Dieses Skript testet automatisch beide HDMI-Sinks."
echo "Du kannst es über SSH ausführen, während der Monitor abgesteckt ist."
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Stecke den Monitor ab, bevor du fortfährst!"
echo ""
read -p "Monitor abgesteckt? [j] Ja, weiter / [n] Nein, abbrechen: " answer

if [[ ! "$answer" =~ ^[jJ] ]]; then
  echo "Abgebrochen."
  exit 0
fi

echo ""
echo -e "${CYAN}Starte automatischen Test...${NC}"
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

# Beide HDMI-Sinks
HDMI_SINK_1="alsa_output.platform-107c701400.hdmi.hdmi-stereo"  # HDMI-A-1
HDMI_SINK_2="alsa_output.platform-107c706400.hdmi.hdmi-stereo"  # HDMI-A-2

# Finde Test-Datei
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

if [ -z "$TEST_FILE" ]; then
  echo -e "${RED}✗${NC} Keine Test-Datei gefunden"
  exit 1
fi

echo -e "${GREEN}✓${NC} Test-Datei gefunden: $TEST_FILE"
echo ""

# Teste jeden Sink
for sink_name in "$HDMI_SINK_1" "$HDMI_SINK_2"; do
  # Bestimme Port-Info
  if echo "$sink_name" | grep -q "107c701400"; then
    PORT_INFO="HDMI-A-1"
    PORT_NUM="1"
  elif echo "$sink_name" | grep -q "107c706400"; then
    PORT_INFO="HDMI-A-2"
    PORT_NUM="2"
  else
    PORT_INFO="Unbekannt"
    PORT_NUM="?"
  fi
  
  echo -e "${CYAN}=== Test $PORT_NUM: $PORT_INFO ===${NC}"
  echo ""
  
  # Prüfe ob Sink existiert
  if ! $PACTL list sinks short 2>/dev/null | grep -q "$sink_name"; then
    echo -e "${YELLOW}⚠${NC} Sink nicht gefunden: $sink_name"
    echo ""
    echo "Mögliche Ursachen:"
    echo "  - HDMI-A-1 benötigt cmdline.txt-Konfiguration: video=HDMI-A-1:e"
    echo "  - Neustart erforderlich"
    echo ""
    continue
  fi
  
  echo "Setze als Standard-Sink..."
  $PACTL set-default-sink "$sink_name" 2>/dev/null || {
    echo -e "${RED}✗${NC} Fehler beim Setzen des Sinks"
    continue
  }
  
  sleep 1
  
  # Prüfe Lautstärke
  VOLUME=$($PACTL get-sink-volume "$sink_name" 2>/dev/null | head -1 | awk '{print $5}' | sed 's/%//' || echo "0")
  if [ "$VOLUME" -lt 50 ]; then
    echo "Setze Lautstärke auf 70%..."
    $PACTL set-sink-volume "$sink_name" 70% 2>/dev/null || true
  fi
  
  # Prüfe ob stumm geschaltet
  MUTED=$($PACTL get-sink-mute "$sink_name" 2>/dev/null | awk '{print $2}' || echo "no")
  if [ "$MUTED" = "yes" ]; then
    echo "Entstumme..."
    $PACTL set-sink-mute "$sink_name" 0 2>/dev/null || true
  fi
  
  echo ""
  echo -e "${BLUE}→${NC} Spiele Test-Ton ab (3 Sekunden)..."
  echo ""
  echo -e "${YELLOW}HÖRE:${NC} Kommt der Ton aus den Gehäuselautsprechern?"
  echo ""
  
  # Spiele Test-Ton ab
  if command -v paplay >/dev/null 2>&1; then
    paplay --device="$sink_name" "$TEST_FILE" 2>/dev/null &
    PA_PID=$!
    sleep 3
    kill $PA_PID 2>/dev/null || true
  fi
  
  echo ""
  echo -e "${CYAN}Kam der Ton aus den Gehäuselautsprechern?${NC}"
  echo -e "  ${GREEN}[j]${NC} Ja, dieser Sink funktioniert!"
  echo -e "  ${RED}[n]${NC} Nein, kein Ton"
  echo -e "  ${YELLOW}[s]${NC} Überspringen"
  echo ""
  read -p "Deine Antwort (j/n/s): " answer
  
  case "$answer" in
    [jJ]*)
      echo ""
      echo -e "${GREEN}✓${NC} $PORT_INFO führt zu den Gehäuselautsprechern!"
      echo ""
      echo "Setze als Standard-Sink..."
      $PACTL set-default-sink "$sink_name" 2>/dev/null || true
      echo ""
      echo -e "${GREEN}Erfolg!${NC} Der Ton sollte jetzt aus den Gehäuselautsprechern kommen."
      echo ""
      echo "Du kannst den Monitor wieder anschließen."
      exit 0
      ;;
    [nN]*)
      echo -e "${RED}✗${NC} $PORT_INFO funktioniert nicht"
      ;;
    [sS]*)
      echo -e "${YELLOW}→${NC} Übersprungen"
      ;;
    *)
      echo -e "${YELLOW}→${NC} Übersprungen (ungültige Eingabe)"
      ;;
  esac
  
  echo ""
  echo "---"
  echo ""
  sleep 2
done

echo -e "${YELLOW}=== Kein passender Sink gefunden ===${NC}"
echo ""
echo "Mögliche Ursachen:"
echo "  1. Hardware-Problem (Lautsprecher-Verbindungen, Mediaboard)"
echo "  2. Mediaboard benötigt spezielle Konfiguration"
echo "  3. Defektes Mediaboard"
echo ""
echo "Nächste Schritte:"
echo "  1. Prüfe Hardware-Verbindungen (Lautsprecher, PCIe, FPC-Kabel)"
echo "  2. Teste 3,5-mm-Ausgang am Case-Board"
echo "  3. Kontaktiere Freenove-Support: support@freenove.com"
echo ""
echo "Siehe auch: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md"
echo ""
echo -e "${GREEN}Fertig.${NC}"
