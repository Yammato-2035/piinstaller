#!/bin/bash
# PI-Installer: Freenove HDMI-Audio für Gehäuselautsprecher konfigurieren
#
# Konfiguriert HDMI-Audio für Freenove Computer Case.
# Das Mediaboard extrahiert Audio aus HDMI und leitet es an die Gehäuselautsprecher weiter.
# WICHTIG: HDMI-Audio muss aktiv sein, auch wenn kein Monitor angeschlossen ist.
#
# Ausführung: ./scripts/configure-freenove-hdmi-audio.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove HDMI-Audio für Gehäuselautsprecher konfigurieren ===${NC}"
echo ""

# Prüfe ob auf Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
  echo -e "${YELLOW}⚠${NC} Nicht auf Raspberry Pi"
  exit 1
fi

# Prüfe ob Freenove-Gehäuse erkannt wird
FREENOVE_DETECTED=false
for bus in 1 0 6 7; do
  if i2cget -y $bus 0x21 0xfd 2>/dev/null | grep -q .; then
    FREENOVE_DETECTED=true
    break
  fi
done

if [ "$FREENOVE_DETECTED" != true ]; then
  echo -e "${YELLOW}⚠${NC} Freenove-Gehäuse nicht erkannt"
  echo "  Fortsetzen trotzdem..."
  echo ""
fi

# 1. Prüfe verfügbare HDMI-Ports
echo -e "${CYAN}[1] Verfügbare HDMI-Ports prüfen:${NC}"
HDMI_PORTS=$(ls /sys/class/drm/ 2>/dev/null | grep -E "card.*-HDMI|HDMI" || echo "")
if [ -n "$HDMI_PORTS" ]; then
  echo "  Gefundene HDMI-Ports:"
  echo "$HDMI_PORTS" | while IFS= read -r port; do
    STATUS=$(cat "/sys/class/drm/$port/status" 2>/dev/null || echo "unknown")
    echo "    $port: $STATUS"
  done
else
  echo -e "  ${YELLOW}⚠${NC} Keine HDMI-Ports gefunden"
fi
echo ""

# 2. Prüfe WirePlumber/PipeWire Sinks
echo -e "${CYAN}[2] WirePlumber/PipeWire Sinks prüfen:${NC}"
if command -v wpctl >/dev/null 2>&1; then
  echo "  Verfügbare HDMI-Sinks:"
  wpctl status 2>/dev/null | grep -A20 "Sinks:" | grep -i "hdmi" | while IFS= read -r line; do
    echo "    $line"
  done
  
  DEFAULT_SINK=$(wpctl status 2>/dev/null | grep "Default Configured Devices" -A5 | grep "Audio/Sink" | awk '{print $NF}' || echo "")
  if [ -n "$DEFAULT_SINK" ]; then
    echo ""
    echo -e "  ${GREEN}✓${NC} Standard-Sink: $DEFAULT_SINK"
  else
    echo -e "  ${YELLOW}⚠${NC} Kein Standard-Sink gesetzt"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} wpctl nicht gefunden"
fi
echo ""

# 3. Prüfe ALSA-Karten
echo -e "${CYAN}[3] ALSA-Karten prüfen:${NC}"
if command -v aplay >/dev/null 2>&1; then
  aplay -l 2>/dev/null | grep "^card" | while IFS= read -r line; do
    echo "  $line"
  done
else
  echo -e "  ${YELLOW}⚠${NC} aplay nicht gefunden"
fi
echo ""

# 4. Prüfe cmdline.txt für HDMI-Aktivierung
echo -e "${CYAN}[4] Prüfe cmdline.txt für HDMI-Aktivierung:${NC}"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[ ! -f "$CMDLINE_FILE" ] && CMDLINE_FILE="/boot/cmdline.txt"

if [ -f "$CMDLINE_FILE" ]; then
  CMDLINE_CONTENT=$(cat "$CMDLINE_FILE")
  if echo "$CMDLINE_CONTENT" | grep -q "video=HDMI"; then
    echo -e "  ${GREEN}✓${NC} HDMI-Aktivierung in cmdline.txt gefunden:"
    echo "$CMDLINE_CONTENT" | grep -o "video=HDMI[^ ]*" | while IFS= read -r line; do
      echo "    $line"
    done
  else
    echo -e "  ${YELLOW}⚠${NC} Keine HDMI-Aktivierung in cmdline.txt gefunden"
    echo ""
    echo "  Für Freenove-Gehäuse sollte HDMI-Audio aktiv sein, auch wenn kein Monitor"
    echo "  angeschlossen ist. Das Mediaboard extrahiert Audio aus HDMI."
    echo ""
    echo "  Mögliche Lösung: In $CMDLINE_FILE ergänzen:"
    echo "    video=HDMI-A-1:e"
    echo ""
    echo "  Oder mit fixer Auflösung:"
    echo "    video=HDMI-A-1:1920x1080@60D"
    echo ""
    echo -e "  ${BLUE}→${NC} Welcher HDMI-Port? Prüfe mit: ls /sys/class/drm/ | grep HDMI"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} cmdline.txt nicht gefunden"
fi
echo ""

# 5. Konfigurationsvorschlag
echo -e "${CYAN}[5] Konfigurationsvorschlag:${NC}"
echo ""
echo "Für Freenove-Gehäuse:"
echo "  1. HDMI-Audio muss aktiv sein (auch ohne Monitor)"
echo "  2. Standard-Sink sollte auf HDMI gesetzt sein"
echo "  3. Das Mediaboard extrahiert Audio automatisch aus HDMI"
echo ""

if [ "$FREENOVE_DETECTED" = true ]; then
  echo -e "${GREEN}✓${NC} Freenove-Gehäuse erkannt"
  echo ""
  
  # Prüfe ob Standard-Sink gesetzt ist
  if command -v wpctl >/dev/null 2>&1; then
    DEFAULT_SINK=$(wpctl status 2>/dev/null | grep "Default Configured Devices" -A5 | grep "Audio/Sink" | awk '{print $NF}' || echo "")
    if [ -n "$DEFAULT_SINK" ] && echo "$DEFAULT_SINK" | grep -qi "hdmi"; then
      echo -e "${GREEN}✓${NC} Standard-Sink ist bereits auf HDMI gesetzt: $DEFAULT_SINK"
      echo ""
      echo "Konfiguration sollte korrekt sein. Wenn der Ton nicht aus den"
      echo "Gehäuselautsprechern kommt:"
      echo "  1. Prüfe die Lautsprecher-Verbindungen am Case-Adapter-Board"
      echo "  2. Prüfe, ob HDMI-Audio wirklich aktiv ist (auch ohne Monitor)"
      echo "  3. Teste mit: paplay /usr/share/sounds/alsa/Front_Left.wav"
    else
      echo -e "${YELLOW}⚠${NC} Standard-Sink ist nicht auf HDMI gesetzt"
      echo ""
      echo "Setze HDMI als Standard-Sink..."
      
      # Finde HDMI-Sink
      HDMI_SINK=$(wpctl status 2>/dev/null | grep -i "hdmi" | head -1 | awk '{print $1}' | sed 's/\.$//' || echo "")
      if [ -n "$HDMI_SINK" ]; then
        echo "  Gefundener HDMI-Sink: $HDMI_SINK"
        echo "  Setze als Standard..."
        wpctl set-default "$HDMI_SINK" 2>/dev/null && {
          echo -e "  ${GREEN}✓${NC} Standard-Sink gesetzt"
        } || {
          echo -e "  ${RED}✗${NC} Fehler beim Setzen des Standard-Sinks"
        }
      else
        echo -e "  ${YELLOW}⚠${NC} Kein HDMI-Sink gefunden"
        echo "  Möglicherweise ist HDMI-Audio nicht aktiv."
        echo "  Siehe Schritt 4 für cmdline.txt-Konfiguration."
      fi
    fi
  fi
else
  echo -e "${YELLOW}⚠${NC} Freenove-Gehäuse nicht erkannt"
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
