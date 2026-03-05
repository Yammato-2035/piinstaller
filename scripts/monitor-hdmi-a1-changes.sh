#!/bin/bash
# PI-Installer: Überwache Änderungen an HDMI-A-1 enabled-Status
#
# Überwacht, ob und wann HDMI-A-1 auf "disabled" gesetzt wird.
# Nützlich um herauszufinden, welcher Prozess HDMI-A-1 deaktiviert.
#
# Ausführung: ./scripts/monitor-hdmi-a1-changes.sh
# (Beenden mit Ctrl+C)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

ENABLED_FILE="/sys/class/drm/card2-HDMI-A-1/enabled"

if [ ! -f "$ENABLED_FILE" ]; then
  echo -e "${RED}✗${NC} $ENABLED_FILE nicht gefunden"
  exit 1
fi

echo -e "${CYAN}=== Überwache HDMI-A-1 enabled-Status ===${NC}"
echo ""
echo "Überwache: $ENABLED_FILE"
echo "Beenden mit Ctrl+C"
echo ""

CURRENT_STATUS=$(cat "$ENABLED_FILE" 2>/dev/null || echo "unknown")
echo "Aktueller Status: $CURRENT_STATUS"
echo ""
echo "Starte Überwachung..."
echo ""

# Überwache Änderungen
PREVIOUS_STATUS="$CURRENT_STATUS"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

while true; do
  sleep 1
  
  CURRENT_STATUS=$(cat "$ENABLED_FILE" 2>/dev/null || echo "unknown")
  NEW_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  
  if [ "$CURRENT_STATUS" != "$PREVIOUS_STATUS" ]; then
    echo "[$NEW_TIMESTAMP] Status geändert: $PREVIOUS_STATUS → $CURRENT_STATUS"
    
    # Prüfe welche Prozesse auf die Datei zugreifen
    echo "  Prozesse, die auf HDMI-A-1 zugreifen:"
    lsof "$ENABLED_FILE" 2>/dev/null | tail -n +2 | while read -r line; do
      PID=$(echo "$line" | awk '{print $2}')
      CMD=$(ps -p "$PID" -o comm= 2>/dev/null || echo "unknown")
      USER=$(ps -p "$PID" -o user= 2>/dev/null || echo "unknown")
      echo "    PID $PID ($USER): $CMD"
    done || echo "    (keine gefunden)"
    
    # Prüfe Wayland/Wayfire-Prozesse
    echo "  Wayland/Wayfire-Prozesse:"
    ps aux | grep -E "wayfire|wayland|wlr-randr|kms" | grep -v grep | head -5 | while read -r line; do
      echo "    $line"
    done || echo "    (keine gefunden)"
    
    echo ""
    
    PREVIOUS_STATUS="$CURRENT_STATUS"
  fi
done
