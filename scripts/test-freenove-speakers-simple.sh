#!/bin/bash
# PI-Installer: Einfacher Test für Freenove Gehäuselautsprecher
#
# Testet beide HDMI-Sinks und fragt, ob Ton aus den Gehäuselautsprechern kommt.
#
# Ausführung: ./scripts/test-freenove-speakers-simple.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Teste Freenove Gehäuselautsprecher ===${NC}"
echo ""
echo "Dieses Skript testet beide HDMI-Sinks und fragt, ob der Ton"
echo "aus den Gehäuselautsprechern kommt (nicht aus dem HDMI-Monitor)."
echo ""

# Prüfe verfügbare Sinks
SINK_A1="alsa_output.platform-107c701400.hdmi.hdmi-stereo"  # Card 0, HDMI-A-1
SINK_A2="alsa_output.platform-107c706400.hdmi.hdmi-stereo"  # Card 1, HDMI-A-2

ALL_SINKS=$(pactl list short sinks 2>/dev/null || echo "")
SINK_A1_EXISTS=false
SINK_A2_EXISTS=false

if echo "$ALL_SINKS" | grep -q "$SINK_A1"; then
  SINK_A1_EXISTS=true
fi
if echo "$ALL_SINKS" | grep -q "$SINK_A2"; then
  SINK_A2_EXISTS=true
fi

echo -e "${CYAN}Verfügbare HDMI-Sinks:${NC}"
if [ "$SINK_A1_EXISTS" = true ]; then
  echo -e "  ${GREEN}✓${NC} HDMI-A-1 (Card 0): $SINK_A1"
else
  echo -e "  ${RED}✗${NC} HDMI-A-1 (Card 0): Nicht verfügbar"
fi

if [ "$SINK_A2_EXISTS" = true ]; then
  echo -e "  ${GREEN}✓${NC} HDMI-A-2 (Card 1): $SINK_A2"
else
  echo -e "  ${RED}✗${NC} HDMI-A-2 (Card 1): Nicht verfügbar"
fi
echo ""

if [ "$SINK_A1_EXISTS" = false ] && [ "$SINK_A2_EXISTS" = false ]; then
  echo -e "${RED}✗${NC} Keine HDMI-Sinks verfügbar"
  echo ""
  echo "Lösung:"
  echo "  1. Aktiviere Card 0 Profil:"
  echo "     pactl set-card-profile alsa_card.platform-107c701400.hdmi output:hdmi-stereo"
  echo ""
  echo "  2. Starte WirePlumber neu:"
  echo "     systemctl --user restart wireplumber.service"
  exit 1
fi

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

# Teste HDMI-A-1 (Card 0)
if [ "$SINK_A1_EXISTS" = true ]; then
  echo -e "${CYAN}=== Test 1: HDMI-A-1 (Card 0) ===${NC}"
  echo ""
  echo "Aktiviere HDMI-A-1 als Standard-Sink..."
  pactl set-default-sink "$SINK_A1" 2>/dev/null || true
  pactl set-sink-mute "$SINK_A1" 0 2>/dev/null || true
  pactl set-sink-volume "$SINK_A1" 70% 2>/dev/null || true
  
  echo "Spiele Test-Ton ab..."
  echo ""
  echo -e "${YELLOW}WICHTIG:${NC} Prüfe jetzt, ob der Ton aus den Gehäuselautsprechern kommt!"
  echo ""
  
  if paplay --device="$SINK_A1" "$TEST_FILE" 2>/dev/null; then
    echo ""
    read -p "Kam der Ton aus den Gehäuselautsprechern? [j] Ja / [n] Nein: " answer
    
    if [[ "$answer" =~ ^[jJ] ]]; then
      echo ""
      echo -e "${GREEN}✓${NC} HDMI-A-1 (Card 0) funktioniert mit Gehäuselautsprechern!"
      echo ""
      echo "Lösung: Setze HDMI-A-1 als Standard-Sink:"
      echo "  pactl set-default-sink $SINK_A1"
      echo ""
      exit 0
    else
      echo -e "${RED}✗${NC} Ton kam nur aus HDMI-Monitor"
    fi
  else
    echo -e "${RED}✗${NC} Konnte Test-Ton nicht abspielen"
  fi
  echo ""
fi

# Teste HDMI-A-2 (Card 1)
if [ "$SINK_A2_EXISTS" = true ]; then
  echo -e "${CYAN}=== Test 2: HDMI-A-2 (Card 1) ===${NC}"
  echo ""
  echo "Aktiviere HDMI-A-2 als Standard-Sink..."
  pactl set-default-sink "$SINK_A2" 2>/dev/null || true
  pactl set-sink-mute "$SINK_A2" 0 2>/dev/null || true
  pactl set-sink-volume "$SINK_A2" 70% 2>/dev/null || true
  
  echo "Spiele Test-Ton ab..."
  echo ""
  echo -e "${YELLOW}WICHTIG:${NC} Prüfe jetzt, ob der Ton aus den Gehäuselautsprechern kommt!"
  echo ""
  
  if paplay --device="$SINK_A2" "$TEST_FILE" 2>/dev/null; then
    echo ""
    read -p "Kam der Ton aus den Gehäuselautsprechern? [j] Ja / [n] Nein: " answer
    
    if [[ "$answer" =~ ^[jJ] ]]; then
      echo ""
      echo -e "${GREEN}✓${NC} HDMI-A-2 (Card 1) funktioniert mit Gehäuselautsprechern!"
      echo ""
      echo "Lösung: Setze HDMI-A-2 als Standard-Sink:"
      echo "  pactl set-default-sink $SINK_A2"
      echo ""
      exit 0
    else
      echo -e "${RED}✗${NC} Ton kam nur aus HDMI-Monitor"
    fi
  else
    echo -e "${RED}✗${NC} Konnte Test-Ton nicht abspielen"
  fi
  echo ""
fi

echo -e "${CYAN}=== Zusammenfassung ===${NC}"
echo ""
echo "Keiner der HDMI-Sinks hat Audio zu den Gehäuselautsprechern geroutet."
echo ""
echo "Mögliche Ursachen:"
echo "  1. Mediaboard extrahiert Audio nur ohne Monitor"
echo "  2. Hardware-Problem (FPC-Kabel, Lautsprecher-Verbindungen)"
echo "  3. Falls Gehäuse MUTE-Schalter hat: aktiviert?"
echo ""
echo "Nächste Schritte:"
echo "  1. Teste ohne Monitor: ./scripts/test-audio-without-monitor.sh"
echo "  2. Prüfe Hardware-Verbindungen"
echo "  3. Siehe: docs/FREENOVE_MEDIABOARD_NO_AUDIO_FINAL.md"
echo ""
echo -e "${GREEN}Fertig.${NC}"
