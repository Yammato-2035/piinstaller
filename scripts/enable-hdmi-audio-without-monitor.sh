#!/bin/bash
# PI-Installer: HDMI-Audio ohne Monitor aktivieren (für Freenove)
#
# Aktiviert HDMI-Audio auch ohne angeschlossenen Monitor.
# WICHTIG für Freenove: Das Mediaboard extrahiert Audio aus HDMI.
# Wenn kein Monitor erkannt wird, wird HDMI-Audio deaktiviert → kein Ton.
#
# Ausführung: ./scripts/enable-hdmi-audio-without-monitor.sh [HDMI-Port]
# Beispiel: ./scripts/enable-hdmi-audio-without-monitor.sh HDMI-A-1

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== HDMI-Audio ohne Monitor aktivieren (für Freenove) ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${RED}✗${NC} Nicht auf Raspberry Pi"
  exit 1
fi

# Prüfe Root-Rechte
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}✗${NC} Bitte als root ausführen (sudo)"
  exit 1
fi

# Finde cmdline.txt
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

if [ ! -f "$CMDLINE_FILE" ]; then
  echo -e "${RED}✗${NC} cmdline.txt nicht gefunden: $CMDLINE_FILE"
  exit 1
fi

# Prüfe verfügbare HDMI-Ports
echo -e "${CYAN}Verfügbare HDMI-Ports:${NC}"
HDMI_PORTS=$(ls /sys/class/drm/ 2>/dev/null | grep -E "HDMI-A-" || echo "")
if [ -z "$HDMI_PORTS" ]; then
  echo -e "  ${YELLOW}⚠${NC} Keine HDMI-Ports gefunden"
  echo "  Verwende Standard: HDMI-A-1"
  HDMI_PORT="HDMI-A-1"
else
  echo "$HDMI_PORTS" | while IFS= read -r port; do
    STATUS=$(cat "/sys/class/drm/$port/status" 2>/dev/null || echo "unknown")
    echo "  $port: $STATUS"
  done
  HDMI_PORT=$(echo "$HDMI_PORTS" | head -1)
fi
echo ""

# Wenn Port als Argument übergeben wurde, verwende diesen
if [ -n "$1" ]; then
  HDMI_PORT="$1"
fi

echo -e "${CYAN}Verwende HDMI-Port:${NC} $HDMI_PORT"
echo ""

# Backup erstellen
BACKUP_FILE="${CMDLINE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CMDLINE_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✓${NC} Backup erstellt: $BACKUP_FILE"
echo ""

# Prüfe ob bereits konfiguriert
CURRENT_CMDLINE=$(cat "$CMDLINE_FILE")
if echo "$CURRENT_CMDLINE" | grep -q "video=$HDMI_PORT"; then
  echo -e "${GREEN}✓${NC} HDMI-Audio ist bereits aktiviert für $HDMI_PORT"
  echo ""
  echo "Aktuelle Konfiguration:"
  echo "$CURRENT_CMDLINE" | grep -o "video=$HDMI_PORT[^ ]*" | while IFS= read -r line; do
    echo "  $line"
  done
  echo ""
  echo "Falls der Ton weiterhin nicht aus den Gehäuselautsprechern kommt:"
  echo "  1. Prüfe die Lautsprecher-Verbindungen am Case-Adapter-Board"
  echo "  2. Prüfe mit: wpctl status"
  echo "  3. Teste mit: paplay /usr/share/sounds/alsa/Front_Left.wav"
  exit 0
fi

# Entferne alte video=HDMI-Einträge (falls vorhanden)
NEW_CMDLINE=$(echo "$CURRENT_CMDLINE" | sed 's/video=HDMI[^ ]*//g' | sed 's/  */ /g')

# Füge neuen video=HDMI-Eintrag hinzu
# Format: video=HDMI-A-1:e (e = enabled, auch ohne Monitor)
VIDEO_PARAM="video=$HDMI_PORT:e"

# Prüfe ob cmdline.txt mit Newline endet
if [ "$(tail -c 1 "$CMDLINE_FILE")" != "" ]; then
  NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
else
  NEW_CMDLINE="$NEW_CMDLINE $VIDEO_PARAM"
fi

# Schreibe neue cmdline.txt
echo "$NEW_CMDLINE" > "$CMDLINE_FILE"
echo -e "${GREEN}✓${NC} cmdline.txt aktualisiert"
echo ""
echo "Neue Konfiguration:"
echo "  $VIDEO_PARAM"
echo ""
echo -e "${YELLOW}⚠${NC} Neustart erforderlich!"
echo ""
echo "Nach dem Neustart sollte HDMI-Audio aktiv sein, auch wenn kein Monitor"
echo "angeschlossen ist. Das Mediaboard kann dann Audio aus HDMI extrahieren."
echo ""
echo "Alternative (mit fixer Auflösung):"
echo "  video=$HDMI_PORT:1920x1080@60D"
echo ""
echo "Um diese Option zu verwenden, bearbeite $CMDLINE_FILE manuell und"
echo "ändere '$VIDEO_PARAM' zu 'video=$HDMI_PORT:1920x1080@60D'"
echo ""
echo -e "${GREEN}Fertig.${NC} Bitte Neustart durchführen: sudo reboot"
