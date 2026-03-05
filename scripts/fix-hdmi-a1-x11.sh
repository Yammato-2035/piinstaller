#!/bin/bash
# PI-Installer: Aktiviere HDMI-A-1 unter X11
#
# Unter X11 wird HDMI-A-1 möglicherweise von xrandr-Skripten deaktiviert.
# Dieses Skript aktiviert HDMI-A-1 und verhindert, dass es wieder deaktiviert wird.
#
# Ausführung: ./scripts/fix-hdmi-a1-x11.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Aktiviere HDMI-A-1 unter X11 ===${NC}"
echo ""

# Prüfe ob X11 läuft
if [ -z "$DISPLAY" ]; then
  export DISPLAY=:0
fi

if ! xdpyinfo >/dev/null 2>&1; then
  echo -e "${RED}✗${NC} X11 läuft nicht oder DISPLAY nicht gesetzt"
  exit 1
fi

echo -e "${GREEN}✓${NC} X11 läuft (DISPLAY=$DISPLAY)"
echo ""

# 1. Aktiviere HDMI-A-1 auf Kernel-Ebene
echo -e "${CYAN}[1] Aktiviere HDMI-A-1 auf Kernel-Ebene:${NC}"
CURRENT_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
echo "  Aktueller Status: $CURRENT_STATUS"

if [ "$CURRENT_STATUS" != "enabled" ]; then
  if echo "on" | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled >/dev/null 2>&1; then
    sleep 1
    NEW_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
    if [ "$NEW_STATUS" = "enabled" ]; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 auf Kernel-Ebene aktiviert"
    else
      echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 konnte nicht aktiviert werden (Status: $NEW_STATUS)"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} Konnte HDMI-A-1 nicht aktivieren (benötigt sudo)"
  fi
else
  echo "  HDMI-A-1 ist bereits aktiviert"
fi
echo ""

# 2. Aktiviere HDMI-A-1 mit xrandr
echo -e "${CYAN}[2] Aktiviere HDMI-A-1 mit xrandr:${NC}"
if command -v xrandr >/dev/null 2>&1; then
  # Finde HDMI-A-1 Output-Name in xrandr
  XRANDR_OUTPUT=$(xrandr 2>/dev/null | grep -E "HDMI.*connected" | grep -v "disconnected" | head -1 | awk '{print $1}' || echo "")
  
  if [ -z "$XRANDR_OUTPUT" ]; then
    # Versuche verschiedene Namen
    for name in "HDMI-1-1" "HDMI-1" "HDMI-A-1"; do
      if xrandr 2>/dev/null | grep -q "$name"; then
        XRANDR_OUTPUT="$name"
        break
      fi
    done
  fi
  
  if [ -n "$XRANDR_OUTPUT" ]; then
    echo "  Gefundener Output: $XRANDR_OUTPUT"
    
    # Aktiviere mit xrandr
    if xrandr --output "$XRANDR_OUTPUT" --auto 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit xrandr aktiviert"
      sleep 1
      
      # Prüfe Status
      FINAL_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
      if [ "$FINAL_STATUS" = "enabled" ]; then
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 ist jetzt enabled"
      else
        echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 wurde wieder deaktiviert (Status: $FINAL_STATUS)"
        echo "  Möglicherweise wird es von einem xrandr-Skript deaktiviert"
      fi
    else
      echo -e "  ${YELLOW}⚠${NC} Konnte HDMI-A-1 nicht mit xrandr aktivieren"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 Output nicht in xrandr gefunden"
    echo "  Verfügbare Outputs:"
    xrandr 2>/dev/null | grep "connected" | head -5
  fi
else
  echo -e "  ${YELLOW}⚠${NC} xrandr nicht gefunden"
fi
echo ""

# 3. Prüfe xrandr-Skripte, die HDMI-A-1 deaktivieren könnten
echo -e "${CYAN}[3] Prüfe xrandr-Skripte:${NC}"
XRANDR_SCRIPTS=(
  "$HOME/.xprofile"
  "$HOME/.xinitrc"
  "$HOME/.xsessionrc"
  "/etc/X11/xinit/xinitrc.d/*"
)

FOUND_SCRIPTS=false
for script_pattern in "${XRANDR_SCRIPTS[@]}"; do
  for script in $script_pattern; do
    if [ -f "$script" ]; then
      if grep -q "xrandr.*HDMI.*off\|xrandr.*--off" "$script" 2>/dev/null; then
        echo "  Gefunden: $script"
        echo "    Enthält möglicherweise HDMI-A-1 Deaktivierung:"
        grep -n "xrandr.*HDMI\|xrandr.*--off" "$script" 2>/dev/null | head -5 | sed 's/^/      /'
        FOUND_SCRIPTS=true
      fi
    fi
  done
done

if [ "$FOUND_SCRIPTS" = false ]; then
  echo "  Keine xrandr-Skripte gefunden, die HDMI deaktivieren"
fi
echo ""

# 4. Starte WirePlumber neu
echo -e "${CYAN}[4] Starte WirePlumber neu:${NC}"
if systemctl --user restart wireplumber.service 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} WirePlumber neu gestartet"
  sleep 2
else
  echo -e "  ${YELLOW}⚠${NC} Konnte WirePlumber nicht neu starten"
fi
echo ""

# 5. Prüfe ob Card 0 jetzt verfügbar ist
echo -e "${CYAN}[5] Prüfe ob Card 0 verfügbar ist:${NC}"
SINK_COUNT=$(pactl list short sinks 2>/dev/null | grep -c "107c701400" || echo "0")
if [ "$SINK_COUNT" -gt 0 ]; then
  echo -e "  ${GREEN}✓${NC} Card 0 (HDMI-A-1) ist jetzt als Sink verfügbar!"
  echo ""
  echo "  Verfügbare Sinks:"
  pactl list short sinks 2>/dev/null | grep "hdmi" || echo "  (keine gefunden)"
else
  echo -e "  ${YELLOW}⚠${NC} Card 0 ist immer noch nicht als Sink verfügbar"
  echo ""
  echo "  Mögliche Gründe:"
  echo "    - HDMI-A-1 wurde wieder deaktiviert"
  echo "    - Neustart erforderlich (cmdline.txt enthält bereits video=HDMI-A-1:e)"
  echo "    - X11-Skript deaktiviert HDMI-A-1 automatisch"
fi
echo ""

echo -e "${CYAN}Nächste Schritte:${NC}"
echo ""
echo "1. Falls HDMI-A-1 wieder deaktiviert wird:"
echo "   - Prüfe xrandr-Skripte (siehe oben)"
echo "   - Überwache Änderungen: ./scripts/monitor-hdmi-a1-changes.sh"
echo ""
echo "2. Teste Audio:"
echo "   ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo "3. Falls alles fehlschlägt:"
echo "   - Starte das System neu: sudo reboot"
echo ""
echo -e "${GREEN}Fertig.${NC}"
