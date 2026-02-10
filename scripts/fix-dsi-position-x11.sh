#!/bin/bash
# Schneller Fix: DSI-1 Position korrigieren (links vom HDMI)
# Als Benutzer ausführen (nicht sudo): ./fix-dsi-position-x11.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}DSI-1 Position korrigieren (links vom HDMI)${NC}"
echo ""

# Beide Positionen in einem atomaren Befehl (wie unter Wayland pro Output-Name)
echo -e "${CYAN}Setze Framebuffer und beide Ausgaben (DSI 0x1440, HDMI 480x0)${NC}"
xrandr --fb 3920x2240 --output HDMI-1-2 --pos 480x0 --output DSI-1 --pos 0x1440 2>/dev/null || {
  xrandr --fb 3920x2240 2>/dev/null || true
  xrandr --output HDMI-1-2 --pos 480x0
  xrandr --output DSI-1 --pos 0x1440
}

# HDMI-1-1 ausschalten (kein Bildschirm angeschlossen)
if xrandr | grep -q "HDMI-1-1 connected"; then
  echo -e "${CYAN}Deaktiviere HDMI-1-1 (kein Bildschirm angeschlossen)${NC}"
  xrandr --output HDMI-1-1 --off
fi

echo ""
echo -e "${GREEN}Fertig! DSI-1 links unten (0,1440), HDMI-1-2 rechts oben (480,0).${NC}"
echo ""
echo -e "${YELLOW}Prüfe mit: xrandr --listmonitors${NC}"
