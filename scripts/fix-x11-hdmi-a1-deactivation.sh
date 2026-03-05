#!/bin/bash
# PI-Installer: Repariere X11-Skripte, die HDMI-A-1 deaktivieren
#
# Problem: .xprofile und andere X11-Skripte deaktivieren HDMI-A-1 automatisch
# mit "xrandr --output HDMI-1-1 --off", weil dort kein Monitor angeschlossen ist.
# Das verhindert, dass Card 0 als PipeWire-Sink erkannt wird.
#
# Lösung: Entferne oder kommentiere diese Zeilen aus, damit HDMI-A-1 aktiv bleibt.
#
# Ausführung: ./scripts/fix-x11-hdmi-a1-deactivation.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Repariere X11-Skripte, die HDMI-A-1 deaktivieren ===${NC}"
echo ""

# 1. Prüfe .xprofile
echo -e "${CYAN}[1] Prüfe .xprofile:${NC}"
XPROFILE="$HOME/.xprofile"
if [ -f "$XPROFILE" ]; then
  echo "  Gefunden: $XPROFILE"
  
  # Prüfe ob HDMI-1-1 deaktiviert wird
  if grep -q "xrandr.*HDMI-1-1.*--off\|xrandr.*HDMI.*--off" "$XPROFILE" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠${NC} .xprofile deaktiviert HDMI-1-1!"
    echo ""
    echo "  Gefundene Zeilen:"
    grep -n "xrandr.*HDMI.*--off" "$XPROFILE" 2>/dev/null | sed 's/^/    /'
    echo ""
    
    # Backup erstellen
    BACKUP="$XPROFILE.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$XPROFILE" "$BACKUP"
    echo "  Backup erstellt: $BACKUP"
    echo ""
    
    # Entferne oder kommentiere die Zeilen
    echo "  Entferne HDMI-1-1 Deaktivierung..."
    sed -i 's/^\(.*xrandr.*HDMI-1-1.*--off.*\)$/# \1  # DEAKTIVIERT: Für Freenove Mediaboard Audio benötigt/' "$XPROFILE"
    sed -i 's/^\(.*xrandr.*HDMI.*--off.*\)$/# \1  # DEAKTIVIERT: Für Freenove Mediaboard Audio benötigt/' "$XPROFILE"
    
    echo -e "  ${GREEN}✓${NC} HDMI-1-1 Deaktivierung entfernt/kommentiert"
    echo ""
    echo "  Neue .xprofile (relevant):"
    grep -E "HDMI|xrandr" "$XPROFILE" 2>/dev/null | head -10 | sed 's/^/    /'
  else
    echo -e "  ${GREEN}✓${NC} .xprofile deaktiviert HDMI-1-1 nicht"
  fi
else
  echo "  Keine .xprofile gefunden"
fi
echo ""

# 2. Prüfe andere X11-Skripte
echo -e "${CYAN}[2] Prüfe andere X11-Skripte:${NC}"
XRANDR_SCRIPTS=(
  "$HOME/.xinitrc"
  "$HOME/.xsessionrc"
  "$HOME/Documents/PI-Installer/scripts/apply-dual-display-x11-delayed.sh"
)

FOUND_ISSUES=false
for script in "${XRANDR_SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    if grep -q "xrandr.*HDMI-1-1.*--off\|xrandr.*HDMI.*--off" "$script" 2>/dev/null; then
      echo "  Gefunden: $script"
      echo -e "    ${YELLOW}⚠${NC} Deaktiviert HDMI-1-1"
      grep -n "xrandr.*HDMI.*--off" "$script" 2>/dev/null | sed 's/^/      /'
      FOUND_ISSUES=true
      
      # Backup und Reparatur
      BACKUP="$script.backup.$(date +%Y%m%d_%H%M%S)"
      cp "$script" "$BACKUP"
      sed -i 's/^\(.*xrandr.*HDMI-1-1.*--off.*\)$/# \1  # DEAKTIVIERT: Für Freenove Mediaboard Audio benötigt/' "$script"
      sed -i 's/^\(.*xrandr.*HDMI.*--off.*\)$/# \1  # DEAKTIVIERT: Für Freenove Mediaboard Audio benötigt/' "$script"
      echo -e "    ${GREEN}✓${NC} Repariert (Backup: $BACKUP)"
    fi
  fi
done

if [ "$FOUND_ISSUES" = false ]; then
  echo "  Keine anderen problematischen Skripte gefunden"
fi
echo ""

# 3. Aktiviere HDMI-A-1 jetzt
echo -e "${CYAN}[3] Aktiviere HDMI-A-1 jetzt:${NC}"
export DISPLAY=:0

if command -v xrandr >/dev/null 2>&1; then
  # Prüfe ob HDMI-1-1 existiert
  if xrandr 2>/dev/null | grep -q "HDMI-1-1.*connected"; then
    echo "  HDMI-1-1 ist connected, aktiviere..."
    
    # Versuche verschiedene Modi
    if xrandr --output HDMI-1-1 --auto 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit xrandr aktiviert (--auto)"
      sleep 2
    elif xrandr --output HDMI-1-1 --mode 1920x1080 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit xrandr aktiviert (1920x1080)"
      sleep 2
    elif xrandr --output HDMI-1-1 --on 2>/dev/null; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 mit xrandr aktiviert (--on)"
      sleep 2
    else
      echo -e "  ${YELLOW}⚠${NC} Konnte HDMI-A-1 nicht mit xrandr aktivieren"
      echo "  Versuche auf Kernel-Ebene..."
      echo "on" | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled >/dev/null 2>&1 || true
      sleep 2
    fi
    
    # Prüfe Status
    KERNEL_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
    if [ "$KERNEL_STATUS" = "enabled" ]; then
      echo -e "  ${GREEN}✓${NC} HDMI-A-1 ist jetzt enabled"
    else
      echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 ist immer noch disabled (Status: $KERNEL_STATUS)"
      echo "  Möglicherweise wird es von einem anderen Prozess deaktiviert"
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} HDMI-1-1 nicht in xrandr gefunden"
    echo "  Versuche auf Kernel-Ebene..."
    echo "on" | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled >/dev/null 2>&1 || true
    sleep 2
  fi
else
  echo -e "  ${YELLOW}⚠${NC} xrandr nicht gefunden"
  echo "  Versuche auf Kernel-Ebene..."
  echo "on" | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled >/dev/null 2>&1 || true
  sleep 2
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
  echo "    - Neustart erforderlich"
  echo "    - Andere X11-Skripte deaktivieren HDMI-A-1"
fi
echo ""

echo -e "${CYAN}Nächste Schritte:${NC}"
echo ""
echo "1. Melde dich ab und wieder an (damit .xprofile neu geladen wird)"
echo "   Oder starte X11 neu"
echo ""
echo "2. Teste Audio:"
echo "   ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo "3. Falls HDMI-A-1 wieder deaktiviert wird:"
echo "   - Überwache Änderungen: ./scripts/monitor-hdmi-a1-changes.sh"
echo "   - Prüfe andere X11-Skripte"
echo ""
echo -e "${GREEN}Fertig.${NC}"
