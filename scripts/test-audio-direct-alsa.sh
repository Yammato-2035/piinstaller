#!/bin/bash
# PI-Installer: Teste Audio direkt über ALSA (umgeht PipeWire/WirePlumber)
#
# Testet beide ALSA-Karten direkt, um zu prüfen ob das Mediaboard Audio extrahiert,
# auch wenn PipeWire/WirePlumber das Audio-Routing blockiert.
#
# Ausführung: ./scripts/test-audio-direct-alsa.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Teste Audio direkt über ALSA (umgeht PipeWire/WirePlumber) ===${NC}"
echo ""
echo "Dieses Skript testet beide ALSA-Karten direkt, um zu prüfen ob das"
echo "Mediaboard Audio extrahiert, auch wenn PipeWire/WirePlumber das"
echo "Audio-Routing blockiert."
echo ""

# Prüfe ob ALSA-Karten existieren
if [ ! -f "/proc/asound/cards" ]; then
  echo -e "${RED}✗${NC} /proc/asound/cards nicht gefunden"
  exit 1
fi

CARDS=$(cat /proc/asound/cards | grep "^[[:space:]]*[0-9]" | awk '{print $1}' | tr -d '[]' || echo "")

if [ -z "$CARDS" ]; then
  echo -e "${RED}✗${NC} Keine ALSA-Karten gefunden"
  exit 1
fi

echo -e "${CYAN}[1] Gefundene ALSA-Karten:${NC}"
echo "$CARDS" | while read -r card; do
  CARD_INFO=$(cat /proc/asound/cards | grep "^[[:space:]]*$card" | sed 's/^[[:space:]]*//')
  echo "  Card $card: $CARD_INFO"
done
echo ""

# Finde Test-Datei
TEST_FILE=""
for test in /usr/share/sounds/alsa/Front_Left.wav \
            /usr/share/sounds/alsa/Front_Right.wav \
            /usr/share/sounds/alsa/Noise.wav \
            /usr/share/sounds/freedesktop/stereo/bell.oga; do
  if [ -f "$test" ]; then
    TEST_FILE="$test"
    break
  fi
done

if [ -z "$TEST_FILE" ]; then
  echo -e "${RED}✗${NC} Keine Test-Datei gefunden"
  echo "  Installiere: sudo apt install alsa-utils"
  exit 1
fi

echo -e "${GREEN}✓${NC} Test-Datei gefunden: $TEST_FILE"
echo ""

# Teste jede Karte
echo -e "${CYAN}[2] Teste jede ALSA-Karte direkt:${NC}"
echo ""

for card in $CARDS; do
  CARD_INFO=$(cat /proc/asound/cards | grep "^[[:space:]]*$card" | sed 's/^[[:space:]]*//')
  
  if echo "$CARD_INFO" | grep -q "vc4hdmi0"; then
    PORT_INFO="HDMI-A-1 (Card 0)"
  elif echo "$CARD_INFO" | grep -q "vc4hdmi1"; then
    PORT_INFO="HDMI-A-2 (Card 1)"
  else
    PORT_INFO="Unbekannt"
  fi
  
  echo -e "${CYAN}=== Test Card $card: $PORT_INFO ===${NC}"
  echo ""
  
  # Prüfe verfügbare Geräte
  DEVICES=$(aplay -l 2>/dev/null | grep "^card $card:" | awk '{print $3}' | sed 's/\[//;s/\]//' || echo "")
  
  if [ -z "$DEVICES" ]; then
    echo -e "  ${YELLOW}⚠${NC} Keine Geräte für Card $card gefunden"
    echo ""
    continue
  fi
  
  echo "  Verfügbare Geräte: $DEVICES"
  echo ""
  
  # Teste Device 0
  echo "  Teste Device 0 (hw:$card,0)..."
  
  # Prüfe Format
  FORMAT_OUTPUT=$(aplay -D hw:$card,0 --dump-hw-params /dev/zero 2>&1 || echo "")
  if echo "$FORMAT_OUTPUT" | grep -q "IEC958"; then
    echo -e "    ${YELLOW}⚠${NC} Card $card läuft im IEC958-Modus (S/PDIF)"
    echo "    Das Mediaboard könnte IEC958-Signale extrahieren"
  fi
  
  # Spiele Test-Ton
  echo "    Spiele Test-Ton ab..."
  echo ""
  echo -e "    ${YELLOW}WICHTIG:${NC} Prüfe jetzt, ob Ton aus den Gehäuselautsprechern kommt!"
  echo ""
  
  if aplay -D hw:$card,0 "$TEST_FILE" 2>&1; then
    echo ""
    echo -e "    ${GREEN}✓${NC} Test-Ton abgespielt"
    echo ""
    read -p "    Kam der Ton aus den Gehäuselautsprechern? [j] Ja / [n] Nein: " answer
    
    if [[ "$answer" =~ ^[jJ] ]]; then
      echo ""
      echo -e "    ${GREEN}✓${NC} Card $card ($PORT_INFO) funktioniert mit Gehäuselautsprechern!"
      echo ""
      echo "    Lösung: Verwende Card $card direkt über ALSA:"
      echo "      aplay -D hw:$card,0 <audio-file>"
      echo ""
      echo "    Oder konfiguriere PipeWire, um Card $card zu verwenden:"
      echo "      pactl set-card-profile alsa_card.platform-$(echo "$CARD_INFO" | grep -o 'platform-[0-9a-f]*' | head -1) output:hdmi-stereo"
      echo ""
      exit 0
    else
      echo -e "    ${RED}✗${NC} Ton kam nur aus HDMI-Monitor"
    fi
  else
    echo -e "    ${RED}✗${NC} Konnte Test-Ton nicht abspielen"
  fi
  
  echo ""
done

echo -e "${CYAN}[3] Zusammenfassung:${NC}"
echo ""
echo "Keine der ALSA-Karten hat Audio zu den Gehäuselautsprechern geroutet."
echo ""
echo "Mögliche Ursachen:"
echo "  1. Mediaboard extrahiert Audio nur ohne Monitor"
echo "  2. Hardware-Problem (FPC-Kabel, Lautsprecher-Verbindungen)"
echo "  3. Falls Gehäuse MUTE-Schalter hat: aktiviert?"
echo "  4. Mediaboard benötigt spezielle Initialisierung"
echo ""
echo "Nächste Schritte:"
echo "  1. Teste ohne Monitor: ./scripts/test-audio-without-monitor.sh"
echo "  2. Prüfe Hardware-Verbindungen"
echo "  3. Falls vorhanden: MUTE-Schalter am Gehäuse prüfen"
echo "  4. Siehe: docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md"
echo ""
echo -e "${GREEN}Fertig.${NC}"
