#!/bin/bash
# PI-Installer: Erzwinge WirePlumber-Sink für HDMI-A-1
#
# Versucht, WirePlumber dazu zu bringen, einen Sink für Card 0 (HDMI-A-1) zu erstellen.
#
# Ausführung: ./scripts/force-wireplumber-hdmi-a1-sink.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Erzwinge WirePlumber-Sink für HDMI-A-1 ===${NC}"
echo ""

# Prüfe ob Card 0 existiert
ALSA_CARDS=$(aplay -l 2>/dev/null || echo "")
if echo "$ALSA_CARDS" | grep -q "^card 0"; then
  echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist als ALSA-Karte verfügbar"
  echo "$ALSA_CARDS" | grep "^card 0"
else
  # Prüfe auch /proc/asound/cards
  if grep -q "^ 0 \[vc4hdmi0" /proc/asound/cards 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Card 0 (HDMI-A-1) ist in /proc/asound/cards vorhanden"
    grep "^ 0 \[vc4hdmi0" /proc/asound/cards
  else
    echo -e "${RED}✗${NC} Card 0 (HDMI-A-1) ist nicht als ALSA-Karte verfügbar"
    echo "  Lösung: Neustart durchführen (sudo reboot)"
    exit 1
  fi
fi
echo ""

# Prüfe ob wpctl verfügbar ist
if ! command -v wpctl >/dev/null 2>&1; then
  echo -e "${RED}✗${NC} wpctl nicht gefunden"
  exit 1
fi

# Prüfe verfügbare Devices
echo -e "${CYAN}[1] Verfügbare WirePlumber-Devices:${NC}"
wpctl status 2>/dev/null | grep -A20 "Devices:" | head -25
echo ""

# Versuche Card 0 zu finden
echo -e "${CYAN}[2] Suche nach Card 0 in WirePlumber:${NC}"
CARD0_DEVICE=$(wpctl status 2>/dev/null | grep -i "card.*0\|107c701400\|vc4hdmi0" | head -1 || echo "")
if [ -n "$CARD0_DEVICE" ]; then
  echo "  Gefunden: $CARD0_DEVICE"
else
  echo -e "  ${YELLOW}⚠${NC} Card 0 nicht in WirePlumber-Devices gefunden"
fi
echo ""

# Prüfe WirePlumber-Konfiguration
echo -e "${CYAN}[3] WirePlumber-Konfiguration prüfen:${NC}"
WIREPLUMBER_CONFIG_DIRS=(
  "$HOME/.config/wireplumber"
  "/etc/wireplumber"
  "/usr/share/wireplumber"
)

FOUND_CONFIG=false
for config_dir in "${WIREPLUMBER_CONFIG_DIRS[@]}"; do
  if [ -d "$config_dir" ]; then
    echo "  Gefunden: $config_dir"
    FOUND_CONFIG=true
    
    # Suche nach ALSA-Konfiguration
    ALSA_CONFIG=$(find "$config_dir" -name "*alsa*" -o -name "*monitor*" 2>/dev/null | head -5 || echo "")
    if [ -n "$ALSA_CONFIG" ]; then
      echo "    ALSA-Konfiguration:"
      echo "$ALSA_CONFIG" | while IFS= read -r file; do
        echo "      $file"
      done
    fi
  fi
done

if [ "$FOUND_CONFIG" = false ]; then
  echo -e "  ${YELLOW}⚠${NC} Keine WirePlumber-Konfiguration gefunden"
fi
echo ""

# Versuche WirePlumber neu zu starten
echo -e "${CYAN}[4] WirePlumber neu starten:${NC}"
if systemctl --user restart wireplumber 2>/dev/null; then
  echo -e "${GREEN}✓${NC} WirePlumber neu gestartet"
  sleep 3
  
  # Prüfe ob Card 0 jetzt als Sink verfügbar ist
  echo ""
  echo -e "${CYAN}[5] Prüfe Sinks nach Neustart:${NC}"
  ALL_SINKS=$(pactl list sinks short 2>/dev/null || echo "")
  if echo "$ALL_SINKS" | grep -q "107c701400"; then
    echo -e "${GREEN}✓${NC} HDMI-A-1 ist jetzt als PipeWire-Sink verfügbar!"
    echo "$ALL_SINKS" | grep "107c701400"
  else
    echo -e "${YELLOW}⚠${NC} HDMI-A-1 ist immer noch nicht als PipeWire-Sink verfügbar"
    echo ""
    echo "Mögliche Ursachen:"
    echo "  1. WirePlumber erkennt Card 0 nicht automatisch"
    echo "  2. Card 0 läuft im IEC958-Modus (S/PDIF) und wird nicht als PCM-Sink erkannt"
    echo "  3. WirePlumber benötigt eine explizite Konfiguration"
    echo ""
    echo "Lösungen:"
    echo "  1. Neustart durchführen: sudo reboot"
    echo "  2. WirePlumber-Konfiguration anpassen (siehe Dokumentation)"
    echo "  3. Prüfe ob Card 0 im IEC958-Modus läuft:"
    echo "     aplay -D hw:0,0 --dump-hw-params /dev/zero"
  fi
else
  echo -e "${RED}✗${NC} Fehler beim Neustarten von WirePlumber"
fi

echo ""
echo -e "${GREEN}Fertig.${NC}"
