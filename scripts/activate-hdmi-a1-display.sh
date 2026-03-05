#!/bin/bash
# PI-Installer: Aktiviere HDMI-A-1 Display
#
# Aktiviert HDMI-A-1 Display, damit Card 0 als PipeWire-Sink erkannt wird.
# Nützlich wenn cmdline.txt bereits video=HDMI-A-1:e enthält, aber HDMI-A-1
# trotzdem "disabled" ist.
#
# Ausführung: ./scripts/activate-hdmi-a1-display.sh
# (Benötigt sudo-Rechte für HDMI-A-1 Aktivierung)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Aktiviere HDMI-A-1 Display ===${NC}"
echo ""

if [ ! -f "/sys/class/drm/card2-HDMI-A-1/enabled" ]; then
  echo -e "${RED}✗${NC} /sys/class/drm/card2-HDMI-A-1/enabled nicht gefunden"
  exit 1
fi

CURRENT_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
echo "Aktueller Status: $CURRENT_STATUS"
echo ""

if [ "$CURRENT_STATUS" = "enabled" ]; then
  echo -e "${GREEN}✓${NC} HDMI-A-1 ist bereits aktiviert"
  exit 0
fi

echo "Aktiviere HDMI-A-1 Display..."
# Prüfe ob sudo verfügbar ist
if command -v sudo >/dev/null 2>&1; then
  if sudo -n true 2>/dev/null; then
    # Sudo-Rechte bereits vorhanden (z.B. durch sudo-Vorgänger)
    SUDO_CMD="sudo"
  else
    # Frage nach sudo-Passwort
    echo "Benötigt sudo-Rechte für HDMI-A-1 Aktivierung..."
    SUDO_CMD="sudo"
  fi
else
  # Kein sudo verfügbar, versuche direkt (falls als root)
  if [ "$(id -u)" -eq 0 ]; then
    SUDO_CMD=""
  else
    SUDO_CMD="sudo"
  fi
fi

if $SUDO_CMD bash -c "echo on > /sys/class/drm/card2-HDMI-A-1/enabled" 2>/dev/null; then
  sleep 2
  NEW_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
  
  if [ "$NEW_STATUS" = "enabled" ]; then
    echo -e "${GREEN}✓${NC} HDMI-A-1 Display aktiviert"
    echo ""
    echo "Starte WirePlumber neu, damit Card 0 erkannt wird..."
    if systemctl --user restart wireplumber.service 2>/dev/null; then
      sleep 2
      echo -e "${GREEN}✓${NC} WirePlumber neu gestartet"
      echo ""
      echo "Prüfe ob Card 0 jetzt als Sink verfügbar ist..."
      sleep 1
      
      SINK_COUNT=$(pactl list short sinks 2>/dev/null | grep -c "107c701400" || echo "0")
      if [ "$SINK_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist jetzt als Sink verfügbar!"
        echo ""
        echo "Verfügbare Sinks:"
        pactl list short sinks 2>/dev/null | grep "hdmi" || echo "  (keine gefunden)"
      else
        echo -e "${YELLOW}⚠${NC} Card 0 ist immer noch nicht als Sink verfügbar"
        echo "  Möglicherweise Neustart erforderlich"
      fi
    else
      echo -e "${YELLOW}⚠${NC} Konnte WirePlumber nicht neu starten"
    fi
  else
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 konnte nicht aktiviert werden (Status: $NEW_STATUS)"
    echo "  Möglicherweise Neustart erforderlich (cmdline.txt enthält bereits video=HDMI-A-1:e)"
  fi
else
  echo -e "${RED}✗${NC} Konnte HDMI-A-1 nicht aktivieren"
  echo ""
  echo "Mögliche Lösungen:"
  echo ""
  echo "1. Führe mit sudo aus:"
  echo "   sudo ./scripts/activate-hdmi-a1-display.sh"
  echo ""
  echo "2. Oder führe manuell aus:"
  echo "   echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled"
  echo "   systemctl --user restart wireplumber.service"
  echo ""
  echo "3. Oder starte das System neu (cmdline.txt enthält bereits video=HDMI-A-1:e):"
  echo "   sudo reboot"
  echo ""
  exit 1
fi

echo ""
echo -e "${CYAN}Nächste Schritte:${NC}"
echo ""
echo "1. Teste beide HDMI-Sinks:"
echo "   ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo "2. Falls Card 0 immer noch nicht verfügbar ist:"
echo "   - Starte das System neu: sudo reboot"
echo "   - cmdline.txt enthält bereits video=HDMI-A-1:e"
echo ""
echo -e "${GREEN}Fertig.${NC}"
