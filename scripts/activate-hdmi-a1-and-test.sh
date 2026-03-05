#!/bin/bash
# PI-Installer: Aktiviere HDMI-A-1 und teste Audio
#
# Aktiviert HDMI-A-1 auf Kernel-Ebene, startet WirePlumber neu und testet,
# ob Card 0 jetzt als PipeWire-Sink verfügbar ist.
#
# Ausführung: ./scripts/activate-hdmi-a1-and-test.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Aktiviere HDMI-A-1 und teste Audio ===${NC}"
echo ""

# 1. Aktiviere HDMI-A-1 auf Kernel-Ebene
echo -e "${CYAN}[1] Aktiviere HDMI-A-1 auf Kernel-Ebene:${NC}"
CURRENT_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
echo "  Aktueller Status: $CURRENT_STATUS"

if [ "$CURRENT_STATUS" != "enabled" ]; then
  echo "  Aktiviere HDMI-A-1..."
  
  # Prüfe ob wir bereits root sind
  if [ "$(id -u)" -eq 0 ]; then
    # Als root ausführen
    if echo "on" > /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null; then
      sleep 2
      NEW_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
      if [ "$NEW_STATUS" = "enabled" ]; then
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 aktiviert"
      else
        echo -e "  ${RED}✗${NC} HDMI-A-1 konnte nicht aktiviert werden (Status: $NEW_STATUS)"
        echo "  Möglicherweise wird es von einem anderen Prozess deaktiviert"
        exit 1
      fi
    else
      echo -e "  ${RED}✗${NC} Konnte HDMI-A-1 nicht aktivieren"
      exit 1
    fi
  else
    # Mit sudo ausführen
    if echo "on" | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled >/dev/null 2>&1; then
      sleep 2
      NEW_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
      if [ "$NEW_STATUS" = "enabled" ]; then
        echo -e "  ${GREEN}✓${NC} HDMI-A-1 aktiviert"
      else
        echo -e "  ${RED}✗${NC} HDMI-A-1 konnte nicht aktiviert werden (Status: $NEW_STATUS)"
        echo "  Möglicherweise wird es von einem anderen Prozess deaktiviert"
        exit 1
      fi
    else
      echo -e "  ${RED}✗${NC} Konnte HDMI-A-1 nicht aktivieren (benötigt sudo)"
      echo ""
      echo "  Führe manuell aus:"
      echo "    echo on | sudo tee /sys/class/drm/card2-HDMI-A-1/enabled"
      exit 1
    fi
  fi
else
  echo "  HDMI-A-1 ist bereits aktiviert"
fi
echo ""

# 2. Starte WirePlumber neu
echo -e "${CYAN}[2] Starte WirePlumber neu:${NC}"
if systemctl --user restart wireplumber.service 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} WirePlumber neu gestartet"
  sleep 3
else
  echo -e "  ${YELLOW}⚠${NC} Konnte WirePlumber nicht neu starten"
fi
echo ""

# 3. Prüfe ob Card 0 jetzt verfügbar ist
echo -e "${CYAN}[3] Prüfe ob Card 0 verfügbar ist:${NC}"
SINK_COUNT=$(pactl list short sinks 2>/dev/null | grep -c "107c701400" || echo "0")
SINK_COUNT=${SINK_COUNT:-0}

if [ "$SINK_COUNT" -gt 0 ]; then
  echo -e "  ${GREEN}✓${NC} Card 0 (HDMI-A-1) ist jetzt als Sink verfügbar!"
  echo ""
  echo "  Verfügbare HDMI-Sinks:"
  pactl list short sinks 2>/dev/null | grep "hdmi" || echo "  (keine gefunden)"
  echo ""
  echo -e "${CYAN}[4] Teste beide HDMI-Sinks:${NC}"
  echo ""
  echo "  Führe jetzt den Audio-Test aus:"
  echo "  ./scripts/test-both-hdmi-sinks.sh"
  echo ""
else
  echo -e "  ${YELLOW}⚠${NC} Card 0 ist immer noch nicht als Sink verfügbar"
  echo ""
  echo "  Verfügbare Sinks:"
  pactl list short sinks 2>/dev/null | grep "hdmi" || echo "  (keine gefunden)"
  echo ""
  echo "  Mögliche Gründe:"
  echo "    - HDMI-A-1 wurde wieder deaktiviert"
  echo "    - WirePlumber erstellt keinen Sink für disabled HDMI-Ports"
  echo "    - Neustart erforderlich"
  echo ""
  echo "  Prüfe Status:"
  echo "    cat /sys/class/drm/card2-HDMI-A-1/enabled"
fi
echo ""

echo -e "${CYAN}Nächste Schritte:${NC}"
echo ""
if [ "$SINK_COUNT" -gt 0 ]; then
  echo "1. Teste beide HDMI-Sinks:"
  echo "   ./scripts/test-both-hdmi-sinks.sh"
  echo ""
  echo "2. Falls HDMI-A-1 wieder deaktiviert wird:"
  echo "   - Überwache Änderungen: ./scripts/monitor-hdmi-a1-changes.sh"
  echo "   - Prüfe ob andere Skripte HDMI-A-1 deaktivieren"
else
  echo "1. Prüfe ob HDMI-A-1 aktiviert bleibt:"
  echo "   cat /sys/class/drm/card2-HDMI-A-1/enabled"
  echo ""
  echo "2. Falls HDMI-A-1 wieder deaktiviert wird:"
  echo "   - Überwache Änderungen: ./scripts/monitor-hdmi-a1-changes.sh"
  echo "   - Prüfe ob andere Skripte HDMI-A-1 deaktivieren"
  echo ""
  echo "3. Falls alles fehlschlägt:"
  echo "   - Starte das System neu: sudo reboot"
fi
echo ""
echo -e "${GREEN}Fertig.${NC}"
