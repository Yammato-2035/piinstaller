#!/bin/bash
# PI-Installer: HDMI-A-1 Display aktivieren
#
# Aktiviert HDMI-A-1 explizit, auch wenn dort kein Monitor angeschlossen ist.
# Dies könnte auch die Audio-Karte aktivieren.
#
# Ausführung: ./scripts/enable-hdmi-a1-display.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== HDMI-A-1 Display aktivieren ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${RED}✗${NC} Nicht auf Raspberry Pi"
  exit 1
fi

# Prüfe aktuellen Status
echo -e "${CYAN}Aktueller Status:${NC}"
if [ -f "/sys/class/drm/card2-HDMI-A-1/status" ]; then
  STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/status 2>/dev/null || echo "unknown")
  ENABLED=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
  echo "  HDMI-A-1: Status=$STATUS, Enabled=$ENABLED"
  
  if [ "$ENABLED" = "disabled" ]; then
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist disabled"
    echo ""
    echo "Versuche HDMI-A-1 zu aktivieren..."
    
    # Versuche mit wlr-randr (Wayland)
    if command -v wlr-randr >/dev/null 2>&1; then
      echo "  Verwende wlr-randr..."
      wlr-randr --output HDMI-A-1 --on 2>/dev/null && {
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit wlr-randr aktiviert"
      } || {
        echo -e "  ${YELLOW}⚠${NC} wlr-randr konnte HDMI-A-1 nicht aktivieren"
      }
    fi
    
    # Versuche mit xrandr (X11)
    if command -v xrandr >/dev/null 2>&1; then
      echo "  Verwende xrandr..."
      xrandr --output HDMI-A-1 --auto 2>/dev/null && {
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit xrandr aktiviert"
      } || {
        echo -e "  ${YELLOW}⚠${NC} xrandr konnte HDMI-A-1 nicht aktivieren"
      }
    fi
    
    # Warte kurz
    sleep 2
    
    # Prüfe Status erneut
    NEW_ENABLED=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
    if [ "$NEW_ENABLED" = "enabled" ]; then
      echo -e "${GREEN}✓${NC} HDMI-A-1 ist jetzt enabled"
    else
      echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist immer noch disabled"
      echo ""
      echo "Mögliche Lösungen:"
      echo "  1. Prüfe cmdline.txt: video=HDMI-A-1:e sollte vorhanden sein"
      echo "  2. Neustart durchführen: sudo reboot"
      echo "  3. Prüfe Kernel-Logs: sudo dmesg | grep -i hdmi"
    fi
  else
    echo -e "${GREEN}✓${NC} HDMI-A-1 ist bereits enabled"
  fi
else
  echo -e "${RED}✗${NC} HDMI-A-1 nicht gefunden in /sys/class/drm/"
fi
echo ""

# Prüfe ALSA-Karten nach Aktivierung
echo -e "${CYAN}ALSA-Karten nach Aktivierung:${NC}"
ALSA_CARDS=$(aplay -l 2>/dev/null || echo "")
if echo "$ALSA_CARDS" | grep -q "^card 0"; then
  echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist jetzt als ALSA-Karte verfügbar"
  echo "$ALSA_CARDS" | grep "^card 0"
else
  echo -e "${YELLOW}⚠${NC} Card 0 (HDMI-A-1) ist immer noch nicht als ALSA-Karte verfügbar"
fi
echo ""

# Prüfe PipeWire-Sinks
echo -e "${CYAN}PipeWire-Sinks:${NC}"
if command -v pactl >/dev/null 2>&1; then
  ALL_SINKS=$(pactl list sinks short 2>/dev/null || echo "")
  if echo "$ALL_SINKS" | grep -q "107c701400"; then
    echo -e "${GREEN}✓${NC} HDMI-A-1 ist jetzt als PipeWire-Sink verfügbar"
    echo "$ALL_SINKS" | grep "107c701400"
  else
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist immer noch nicht als PipeWire-Sink verfügbar"
    echo ""
    echo "Mögliche Lösungen:"
    echo "  1. WirePlumber neu starten: systemctl --user restart wireplumber"
    echo "  2. Neustart durchführen: sudo reboot"
  fi
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
