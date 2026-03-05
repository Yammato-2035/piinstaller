#!/bin/bash
# PI-Installer: Komplette Diagnose wenn kein Ton aus Gehäuselautsprechern kommt
#
# Führt alle relevanten Diagnose-Schritte durch und gibt konkrete Lösungsvorschläge.
#
# Ausführung: ./scripts/diagnose-no-audio-complete.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Komplette Audio-Diagnose: Kein Ton aus Gehäuselautsprechern ===${NC}"
echo ""

# 1. HDMI-A-1 Status
echo -e "${CYAN}[1] HDMI-A-1 Status:${NC}"
HDMI_A1_ENABLED=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
HDMI_A1_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/status 2>/dev/null || echo "unknown")

echo "  Status: $HDMI_A1_STATUS"
echo "  Enabled: $HDMI_A1_ENABLED"

if [ "$HDMI_A1_ENABLED" = "enabled" ]; then
  echo -e "  ${GREEN}✓${NC} HDMI-A-1 ist aktiviert"
else
  echo -e "  ${RED}✗${NC} HDMI-A-1 ist disabled"
  echo "  → Lösung: EDID erzwingen und Neustart"
fi
echo ""

# 2. Verfügbare Sinks
echo -e "${CYAN}[2] Verfügbare HDMI-Sinks:${NC}"
SINK_A1=$(pactl list short sinks 2>/dev/null | grep "107c701400" | awk '{print $2}' | head -1)
SINK_A2=$(pactl list short sinks 2>/dev/null | grep "107c706400" | awk '{print $2}' | head -1)

if [ -n "$SINK_A1" ]; then
  SINK_A1_STATE=$(pactl list short sinks 2>/dev/null | grep "107c701400" | awk '{print $NF}')
  echo -e "  ${GREEN}✓${NC} HDMI-A-1 Sink: $SINK_A1 ($SINK_A1_STATE)"
else
  echo -e "  ${RED}✗${NC} HDMI-A-1 Sink: Nicht verfügbar"
fi

if [ -n "$SINK_A2" ]; then
  SINK_A2_STATE=$(pactl list short sinks 2>/dev/null | grep "107c706400" | awk '{print $NF}')
  echo -e "  ${GREEN}✓${NC} HDMI-A-2 Sink: $SINK_A2 ($SINK_A2_STATE)"
else
  echo -e "  ${RED}✗${NC} HDMI-A-2 Sink: Nicht verfügbar"
fi
echo ""

# 3. Standard-Sink
echo -e "${CYAN}[3] Standard-Sink:${NC}"
DEFAULT_SINK=$(pactl get-default-sink 2>/dev/null || echo "none")
echo "  $DEFAULT_SINK"

if echo "$DEFAULT_SINK" | grep -q "107c701400"; then
  echo -e "  ${GREEN}✓${NC} Standard-Sink ist HDMI-A-1 (Card 0)"
elif echo "$DEFAULT_SINK" | grep -q "107c706400"; then
  echo -e "  ${YELLOW}⚠${NC} Standard-Sink ist HDMI-A-2 (Card 1) - sollte HDMI-A-1 sein"
else
  echo -e "  ${RED}✗${NC} Standard-Sink ist nicht HDMI-A-1"
fi
echo ""

# 4. Card 0 Profil
echo -e "${CYAN}[4] Card 0 (HDMI-A-1) Profil:${NC}"
CARD_0=$(pactl list cards short | grep "107c701400" | awk '{print $1}' | head -1)

if [ -n "$CARD_0" ]; then
  ACTIVE_PROFILE=$(pactl list cards | grep -A 20 "Card #$CARD_0" | grep "Active Profile" | awk '{print $3}' || echo "unknown")
  echo "  Card: $CARD_0"
  echo "  Active Profile: $ACTIVE_PROFILE"
  
  if [ "$ACTIVE_PROFILE" = "output:hdmi-stereo" ]; then
    echo -e "  ${GREEN}✓${NC} Profil ist aktiviert"
  else
    echo -e "  ${RED}✗${NC} Profil ist nicht aktiviert (aktuell: $ACTIVE_PROFILE)"
    echo "  → Lösung: ./scripts/activate-hdmi-a1-sink.sh"
  fi
else
  echo -e "  ${RED}✗${NC} Card 0 nicht gefunden"
fi
echo ""

# 5. EDID-Konfiguration
echo -e "${CYAN}[5] EDID-Konfiguration:${NC}"
if grep -q "hdmi_edid_file=1" /boot/firmware/config.txt 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} hdmi_edid_file=1 vorhanden"
else
  echo -e "  ${RED}✗${NC} hdmi_edid_file=1 fehlt"
  echo "  → Lösung: sudo ./scripts/fix-freenove-audio-final.sh"
fi

if grep -q "hdmi_force_hotplug=1" /boot/firmware/config.txt 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} hdmi_force_hotplug=1 vorhanden"
else
  echo -e "  ${RED}✗${NC} hdmi_force_hotplug=1 fehlt"
fi

if [ -f "/boot/firmware/edid.dat" ]; then
  EDID_SIZE=$(wc -c < /boot/firmware/edid.dat 2>/dev/null || echo "0")
  if [ "$EDID_SIZE" -gt 128 ]; then
    echo -e "  ${GREEN}✓${NC} EDID-Datei vorhanden ($EDID_SIZE Bytes)"
  else
    echo -e "  ${YELLOW}⚠${NC} EDID-Datei zu klein ($EDID_SIZE Bytes)"
  fi
else
  echo -e "  ${RED}✗${NC} EDID-Datei nicht gefunden"
  echo "  → Lösung: sudo ./scripts/fix-freenove-audio-final.sh"
fi
echo ""

# 6. X11-Skripte
echo -e "${CYAN}[6] X11-Skripte (falls unter X11):${NC}"
if [ -n "$DISPLAY" ] && echo "$DISPLAY" | grep -q ":"; then
  if grep -q "xrandr.*HDMI-1-1.*--off" ~/.xprofile 2>/dev/null; then
    echo -e "  ${RED}✗${NC} ~/.xprofile deaktiviert HDMI-A-1"
    echo "  → Lösung: ./scripts/fix-x11-hdmi-a1-deactivation.sh"
  else
    echo -e "  ${GREEN}✓${NC} ~/.xprofile OK"
  fi
else
  echo "  Nicht unter X11 (Wayland oder kein Display)"
fi
echo ""

# 7. Zusammenfassung und Lösungsvorschläge
echo -e "${CYAN}[7] Zusammenfassung und Lösungsvorschläge:${NC}"
echo ""

PROBLEMS_FOUND=0

if [ "$HDMI_A1_ENABLED" != "enabled" ]; then
  echo -e "${RED}Problem 1:${NC} HDMI-A-1 ist disabled"
  echo "  Lösung:"
  echo "    1. sudo ./scripts/fix-freenove-audio-final.sh"
  echo "    2. sudo reboot"
  echo "    3. Nach Neustart: ./scripts/activate-hdmi-a1-sink.sh"
  echo ""
  PROBLEMS_FOUND=$((PROBLEMS_FOUND + 1))
fi

if [ -z "$SINK_A1" ]; then
  echo -e "${RED}Problem 2:${NC} HDMI-A-1 Sink nicht verfügbar"
  echo "  Lösung:"
  echo "    ./scripts/activate-hdmi-a1-sink.sh"
  echo ""
  PROBLEMS_FOUND=$((PROBLEMS_FOUND + 1))
fi

if [ -z "$CARD_0" ] || [ "$ACTIVE_PROFILE" != "output:hdmi-stereo" ]; then
  echo -e "${RED}Problem 3:${NC} Card 0 Profil nicht aktiviert"
  echo "  Lösung:"
  echo "    ./scripts/activate-hdmi-a1-sink.sh"
  echo ""
  PROBLEMS_FOUND=$((PROBLEMS_FOUND + 1))
fi

if ! grep -q "hdmi_edid_file=1" /boot/firmware/config.txt 2>/dev/null; then
  echo -e "${RED}Problem 4:${NC} EDID-Konfiguration unvollständig"
  echo "  Lösung:"
  echo "    sudo ./scripts/fix-freenove-audio-final.sh"
  echo "    sudo reboot"
  echo ""
  PROBLEMS_FOUND=$((PROBLEMS_FOUND + 1))
fi

if [ "$PROBLEMS_FOUND" -eq 0 ]; then
  echo -e "${YELLOW}Alle Konfigurationen sehen korrekt aus, aber kein Ton.${NC}"
  echo ""
  echo "Mögliche Ursachen:"
  echo "  1. Mediaboard extrahiert Audio nur ohne Monitor (Hardware-Limitierung)"
  echo "  2. Hardware-Problem (FPC-Kabel, Lautsprecher-Verbindungen)"
  echo "  3. Falls Gehäuse MUTE-Schalter hat: aktiviert?"
  echo ""
  echo "Nächste Schritte:"
  echo "  1. Teste ohne Monitor:"
  echo "     Monitor abstecken"
  echo "     ./scripts/test-freenove-speakers-simple.sh"
  echo ""
  echo "  2. Prüfe Hardware:"
  echo "     - FPC-Kabel zwischen Pi 5 und Mediaboard"
  echo "     - Lautsprecher-Verbindungen am Mediaboard"
  echo "     - Falls vorhanden: MUTE-Schalter am Gehäuse"
  echo ""
  echo "  3. Siehe: docs/FREENOVE_AUDIO_DEEP_ANALYSIS.md"
else
  echo -e "${GREEN}Lösungsschritte gefunden. Bitte die oben genannten Probleme beheben.${NC}"
fi

echo ""
echo -e "${CYAN}Fertig.${NC}"
