#!/bin/bash
# PI-Installer – Test: Pi 5 Dual Display (Wayland)
# Prüft Session-Typ, Ausgaben und schaltet HDMI ein.
# Im Wayland-Terminal auf dem DSI ausführen: ./test-pi5-dual-display-wayland.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== Pi 5 Dual Display – Wayland-Test ===${NC}"
echo ""

# 1. Session-Typ
echo -e "${CYAN}[1] Session-Typ${NC}"
echo "    XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "    WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
  echo -e "    ${GREEN}Wayland aktiv${NC}"
else
  echo -e "    ${YELLOW}X11 – für Wayland: Abmelden → Session wählen → Pix (Wayland)${NC}"
fi
echo ""

# 2. wlr-randr (Wayland)
echo -e "${CYAN}[2] wlr-randr (Wayland Ausgaben)${NC}"
if wlr-randr 2>&1; then
  echo -e "    ${GREEN}wlr-randr OK${NC}"
else
  echo -e "    ${RED}wlr-randr fehlgeschlagen (kein Wayland?)${NC}"
fi
echo ""

# 3. HDMI einschalten (Wayland)
echo -e "${CYAN}[3] HDMI per wlr-randr einschalten${NC}"
if wlr-randr --output HDMI-A-1 --on 2>/dev/null; then
  echo -e "    ${GREEN}HDMI-A-1: eingeschaltet${NC}"
else
  echo -e "    ${YELLOW}HDMI-A-1: Fehler oder nicht vorhanden${NC}"
fi
if wlr-randr --output HDMI-A-2 --on 2>/dev/null; then
  echo -e "    ${GREEN}HDMI-A-2: eingeschaltet${NC}"
else
  echo -e "    ${YELLOW}HDMI-A-2: Fehler oder nicht vorhanden${NC}"
fi
echo ""

# 4. xrandr (X11 Fallback)
echo -e "${CYAN}[4] xrandr (falls X11)${NC}"
if [ "$XDG_SESSION_TYPE" = "x11" ] && xrandr 2>/dev/null | head -20; then
  echo -e "    ${YELLOW}X11 – xrandr verfügbar${NC}"
else
  echo "    xrandr übersprungen (Wayland oder nicht verfügbar)"
fi
echo ""

echo -e "${GREEN}Test abgeschlossen.${NC}"
echo "Falls HDMI jetzt angeht: Autostart sollte nach Reboot funktionieren."
echo "Falls nicht: Prüfe ~/.config/autostart/pi-installer-enable-hdmi.desktop"
