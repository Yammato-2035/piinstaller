#!/bin/bash
# PI-Installer: Diagnose Mediaboard-Verbindung und Audio-Extraktion
#
# Prüft warum das Mediaboard kein Audio von HDMI extrahiert.
#
# Ausführung: ./scripts/diagnose-mediaboard-connection.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${CYAN}=== Mediaboard-Verbindung und Audio-Extraktion – Diagnose ===${NC}"
echo ""

# 1. Prüfe PCIe-Verbindung
echo -e "${CYAN}[1] Prüfe PCIe-Verbindung:${NC}"
PCI_AUDIO=$(lspci | grep -i "audio\|multimedia\|sound" || echo "")
if [ -z "$PCI_AUDIO" ]; then
  echo -e "  ${YELLOW}⚠${NC} Kein PCIe-Audio-Gerät gefunden"
  echo "  Das Mediaboard könnte nicht über PCIe angeschlossen sein"
  echo "  oder wird nicht als separates Audio-Gerät erkannt"
else
  echo -e "  ${GREEN}✓${NC} PCIe-Audio-Gerät gefunden:"
  echo "  $PCI_AUDIO"
fi
echo ""

# 2. Prüfe alle PCIe-Geräte
echo -e "${CYAN}[2] Alle PCIe-Geräte:${NC}"
ALL_PCI=$(lspci | head -20)
if [ -n "$ALL_PCI" ]; then
  echo "$ALL_PCI" | while read -r line; do
    if echo "$line" | grep -qi "multimedia\|audio\|sound\|video"; then
      echo -e "  ${GREEN}→${NC} $line"
    else
      echo "  $line"
    fi
  done
else
  echo -e "  ${RED}✗${NC} Keine PCIe-Geräte gefunden"
fi
echo ""

# 3. Prüfe HDMI-Status
echo -e "${CYAN}[3] HDMI-Port-Status:${NC}"
for port in HDMI-A-1 HDMI-A-2; do
  if [ -f "/sys/class/drm/card2-$port/status" ]; then
    STATUS=$(cat "/sys/class/drm/card2-$port/status" 2>/dev/null || echo "unknown")
    ENABLED=$(cat "/sys/class/drm/card2-$port/enabled" 2>/dev/null || echo "unknown")
    echo "  $port:"
    echo "    Status: $STATUS"
    echo "    Enabled: $ENABLED"
  fi
done
echo ""

# 4. Prüfe ALSA-Karten
echo -e "${CYAN}[4] ALSA-Karten:${NC}"
if [ -f "/proc/asound/cards" ]; then
  cat /proc/asound/cards | while read -r line; do
    if echo "$line" | grep -q "^[[:space:]]*[0-9]"; then
      echo "  $line"
    fi
  done
else
  echo -e "  ${RED}✗${NC} /proc/asound/cards nicht gefunden"
fi
echo ""

# 5. Prüfe PipeWire-Sinks
echo -e "${CYAN}[5] PipeWire-Sinks:${NC}"
SINKS=$(pactl list short sinks 2>/dev/null || echo "")
if [ -n "$SINKS" ]; then
  echo "$SINKS" | while read -r line; do
    if echo "$line" | grep -q "hdmi"; then
      echo -e "  ${GREEN}→${NC} $line"
    else
      echo "  $line"
    fi
  done
else
  echo -e "  ${RED}✗${NC} Keine Sinks gefunden"
fi
echo ""

# 6. Prüfe Freenove I2C-Expansion-Board
echo -e "${CYAN}[6] Freenove I2C-Expansion-Board:${NC}"
FREENOVE_FOUND=false
for bus in 0 1 6 7 2 3 4 5; do
  if i2cget -y $bus 0x21 0xfd 2>/dev/null >/dev/null; then
    echo -e "  ${GREEN}✓${NC} Freenove Expansion-Board gefunden auf I2C-Bus $bus (Adresse 0x21)"
    FREENOVE_FOUND=true
    break
  fi
done
if [ "$FREENOVE_FOUND" = false ]; then
  echo -e "  ${YELLOW}⚠${NC} Freenove Expansion-Board nicht gefunden"
  echo "  Das bedeutet möglicherweise, dass das Gehäuse nicht richtig angeschlossen ist"
fi
echo ""

# 7. Prüfe MUTE-Schalter (falls vorhanden)
echo -e "${CYAN}[7] MUTE/Stummschaltung:${NC}"
echo "  ${YELLOW}⚠${NC} Nicht bei allen Freenove-Gehäusen vorhanden. Falls vorhanden:"
echo "  - Ist der MUTE-Schalter am Gehäuse aktiviert?"
echo "  - Ist der Schalter in der richtigen Position?"
echo ""

# 8. Zusammenfassung
echo -e "${CYAN}[8] Zusammenfassung:${NC}"
echo ""
echo "Befund:"
echo "  - PCIe-Audio-Gerät: $([ -n "$PCI_AUDIO" ] && echo "Gefunden" || echo "Nicht gefunden")"
echo "  - Freenove Expansion-Board: $([ "$FREENOVE_FOUND" = true ] && echo "Gefunden" || echo "Nicht gefunden")"
echo "  - HDMI-Sinks: $(echo "$SINKS" | grep -c "hdmi" || echo "0")"
echo ""
echo "Mögliche Probleme:"
echo "  1. Mediaboard nicht richtig über PCIe/FPC-Kabel angeschlossen"
echo "  2. Mediaboard extrahiert Audio nur ohne Monitor"
echo "  3. Falls Gehäuse MUTE-Schalter hat: aktiviert?"
echo "  4. Lautsprecher nicht richtig am Mediaboard angeschlossen"
echo "  5. Hardware-Problem (defektes Mediaboard)"
echo ""
echo "Nächste Schritte:"
echo "  1. Prüfe Hardware-Verbindungen (FPC-Kabel, Lautsprecher)"
echo "  2. Teste ohne Monitor: ./scripts/test-audio-without-monitor.sh"
echo "  3. Falls vorhanden: MUTE-Schalter am Gehäuse prüfen"
echo "  4. Siehe: docs/FREENOVE_MEDIABOARD_AUDIO_EXTRACTION.md"
echo ""
echo -e "${GREEN}Fertig.${NC}"
