#!/bin/bash
# PI-Installer: Erzwinge HDMI-A-1 als Sink (nach Neustart)
#
# Prüft cmdline.txt und gibt Anweisungen, wie HDMI-A-1 aktiviert wird.
# Nach einem Neustart sollte HDMI-A-1 als Sink verfügbar sein.
#
# Ausführung: ./scripts/force-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== HDMI-A-1 Sink aktivieren ===${NC}"
echo ""

# Prüfe cmdline.txt
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

if [ -f "$CMDLINE_FILE" ]; then
  CMDLINE_CONTENT=$(cat "$CMDLINE_FILE")
  if echo "$CMDLINE_CONTENT" | grep -q "video=HDMI-A-1"; then
    echo -e "${GREEN}✓${NC} cmdline.txt enthält bereits: video=HDMI-A-1"
    echo "$CMDLINE_CONTENT" | grep -o "video=HDMI-A-1[^ ]*" | while IFS= read -r line; do
      echo "  $line"
    done
    echo ""
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist in cmdline.txt konfiguriert, aber noch nicht als Sink verfügbar."
    echo ""
    echo "Das bedeutet:"
    echo "  1. Ein Neustart wurde noch nicht durchgeführt, ODER"
    echo "  2. WirePlumber erstellt den Sink nicht automatisch"
    echo ""
    echo -e "${BLUE}Lösung:${NC}"
    echo "  1. Neustart durchführen:"
    echo "     sudo reboot"
    echo ""
    echo "  2. Nach dem Neustart prüfen:"
    echo "     ./scripts/check-hdmi-a1-sink.sh"
    echo ""
    echo "  3. Falls immer noch nicht verfügbar, WirePlumber-Konfiguration prüfen"
  else
    echo -e "${YELLOW}⚠${NC} cmdline.txt enthält kein video=HDMI-A-1"
    echo ""
    echo "Konfiguriere cmdline.txt..."
    
    if [ "$EUID" -ne 0 ]; then
      echo -e "${RED}✗${NC} Bitte als root ausführen (sudo)"
      exit 1
    fi
    
    # Backup erstellen
    BACKUP_FILE="${CMDLINE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CMDLINE_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} Backup erstellt: $BACKUP_FILE"
    
    # Entferne alte video=HDMI-Einträge (falls vorhanden)
    NEW_CMDLINE=$(echo "$CMDLINE_CONTENT" | sed 's/video=HDMI[^ ]*//g' | sed 's/  */ /g')
    
    # Füge video=HDMI-A-1:e hinzu
    VIDEO_PARAM="video=HDMI-A-1:e"
    if [ "$(tail -c 1 "$CMDLINE_FILE")" != "" ]; then
      NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
    else
      NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
    fi
    
    echo "$NEW_CMDLINE" > "$CMDLINE_FILE"
    echo -e "${GREEN}✓${NC} cmdline.txt aktualisiert: $VIDEO_PARAM"
    echo ""
    echo -e "${YELLOW}⚠${NC} Neustart erforderlich!"
    echo ""
    echo "Nach dem Neustart sollte HDMI-A-1 als Sink verfügbar sein."
  fi
else
  echo -e "${RED}✗${NC} cmdline.txt nicht gefunden: $CMDLINE_FILE"
  exit 1
fi

echo ""
echo -e "${CYAN}Zusammenfassung:${NC}"
echo "  HDMI-A-1 muss in cmdline.txt konfiguriert sein: video=HDMI-A-1:e"
echo "  Nach einem Neustart sollte HDMI-A-1 als Sink verfügbar sein"
echo "  Dann kannst du beide HDMI-Sinks testen:"
echo "    ./scripts/test-both-hdmi-sinks.sh"
echo ""
echo -e "${GREEN}Fertig.${NC}"
