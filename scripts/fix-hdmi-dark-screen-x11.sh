#!/bin/bash
# Fix für dunklen HDMI-Bildschirm unter X11
# Als Benutzer ausführen (nicht sudo): ./fix-hdmi-dark-screen-x11.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}HDMI-1-2 Bildschirm reparieren${NC}"
echo ""

# Verfügbare Modi für HDMI-1-2 anzeigen
echo -e "${CYAN}Verfügbare Modi für HDMI-1-2:${NC}"
xrandr | grep "HDMI-1-2" -A 10 | grep -E "^\s+\d+x\d+" | head -5 | sed 's/^/  /' || echo "  Keine Modi gefunden"
echo ""

# HDMI-1-2 explizit aktivieren und als primär setzen
echo -e "${CYAN}[1] HDMI-1-2 aktivieren und als primär setzen${NC}"
xrandr --output HDMI-1-2 --auto --primary

# Kurz warten
sleep 1

# Position setzen (rechts vom DSI)
DSI_WIDTH=480
echo -e "${CYAN}[2] Position setzen (rechts vom DSI bei ${DSI_WIDTH}x0)${NC}"
xrandr --output HDMI-1-2 --pos ${DSI_WIDTH}x0

# Prüfe ob HDMI jetzt aktiv ist
sleep 1
if xrandr --listmonitors | grep -q "HDMI-1-2"; then
  echo -e "${GREEN}✓ HDMI-1-2 ist aktiv${NC}"
else
  echo -e "${RED}✗ HDMI-1-2 ist nicht aktiv${NC}"
fi

echo ""
echo -e "${CYAN}Aktuelle Monitor-Konfiguration:${NC}"
xrandr --listmonitors 2>/dev/null || echo "  Fehler beim Abrufen der Monitor-Liste"

echo ""
echo -e "${YELLOW}Hinweise:${NC}"
echo -e "  • Falls der Bildschirm immer noch dunkel ist, prüfe:"
echo -e "    - HDMI-Kabel-Verbindung"
echo -e "    - Bildschirm-Einstellungen (Input-Quelle)"
echo -e "    - Verfügbare Auflösungen: xrandr | grep HDMI-1-2 -A 20"
echo ""
