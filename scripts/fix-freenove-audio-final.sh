#!/bin/bash
# PI-Installer: Finale Reparatur für Freenove Mediaboard Audio
#
# Problem: HDMI-A-1 ist "disabled", daher extrahiert das Mediaboard kein Audio.
# Lösung: EDID-Konfiguration vervollständigen und Neustart durchführen.
#
# Ausführung: sudo ./scripts/fix-freenove-audio-final.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

echo -e "${CYAN}=== Finale Reparatur für Freenove Mediaboard Audio ===${NC}"
echo ""

# 1. Prüfe HDMI-A-1 Status
echo -e "${CYAN}[1] Prüfe HDMI-A-1 Status:${NC}"
HDMI_A1_ENABLED=$(cat /sys/class/drm/card2-HDMI-A-1/enabled 2>/dev/null || echo "unknown")
echo "  HDMI-A-1 Status: $HDMI_A1_ENABLED"

if [ "$HDMI_A1_ENABLED" = "enabled" ]; then
  echo -e "  ${GREEN}✓${NC} HDMI-A-1 ist bereits aktiviert"
else
  echo -e "  ${YELLOW}⚠${NC} HDMI-A-1 ist disabled - Neustart erforderlich"
fi
echo ""

# 2. Prüfe EDID-Konfiguration
echo -e "${CYAN}[2] Prüfe EDID-Konfiguration:${NC}"
CONFIG_FILE="/boot/firmware/config.txt"
EDID_FILE="/boot/firmware/edid.dat"

if [ ! -f "$EDID_FILE" ]; then
  echo -e "  ${YELLOW}⚠${NC} EDID-Datei nicht gefunden: $EDID_FILE"
  echo "  Erstelle EDID-Datei von HDMI-A-2..."
  
  if [ -f "/sys/class/drm/card2-HDMI-A-2/edid" ]; then
    cp /sys/class/drm/card2-HDMI-A-2/edid "$EDID_FILE" 2>/dev/null || {
      echo -e "  ${RED}✗${NC} Konnte EDID nicht kopieren"
      exit 1
    }
    echo -e "  ${GREEN}✓${NC} EDID-Datei erstellt"
  else
    echo -e "  ${RED}✗${NC} HDMI-A-2 EDID nicht verfügbar"
    exit 1
  fi
else
  echo -e "  ${GREEN}✓${NC} EDID-Datei vorhanden: $EDID_FILE"
fi
echo ""

# 3. Prüfe config.txt (EDID nur IN der ersten [hdmi0]-Sektion, siehe docs/WHY_EDID_CANNOT_BE_FORCED.md)
echo -e "${CYAN}[3] Prüfe config.txt:${NC}"
NEEDS_UPDATE=false

# Entferne einzeln stehende hdmi_edid_file= / hdmi_drive= Zeilen (stehen oft falsch außerhalb [hdmi0]),
# damit wir sie korrekt in die erste [hdmi0]-Sektion einfügen können (siehe docs/WHY_EDID_CANNOT_BE_FORCED.md)
if grep -q "^hdmi_edid_file=\|^hdmi_drive=" "$CONFIG_FILE"; then
  echo "  Entferne vorhandene hdmi_edid_file/hdmi_drive (werden korrekt in [hdmi0] eingefügt)..."
  sed -i '/^hdmi_edid_file=/d' "$CONFIG_FILE"
  sed -i '/^hdmi_drive=/d' "$CONFIG_FILE"
  NEEDS_UPDATE=true
fi

# Prüfe ob [hdmi0] Sektion existiert
if ! grep -q "^\[hdmi0\]" "$CONFIG_FILE"; then
  echo "  Füge [hdmi0] Sektion hinzu..."
  echo "" >> "$CONFIG_FILE"
  echo "[hdmi0]" >> "$CONFIG_FILE"
  echo "hdmi_force_hotplug=1" >> "$CONFIG_FILE"
  NEEDS_UPDATE=true
fi

# Prüfe ob hdmi_force_hotplug=1 in der ersten [hdmi0]-Sektion vorhanden
if ! grep -A 5 "^\[hdmi0\]" "$CONFIG_FILE" | head -6 | grep -q "hdmi_force_hotplug=1"; then
  echo "  Füge hdmi_force_hotplug=1 in [hdmi0] hinzu..."
  sed -i '/^\[hdmi0\]/a hdmi_force_hotplug=1' "$CONFIG_FILE"
  NEEDS_UPDATE=true
fi

# EDID-Optionen nur direkt in der ERSTEN [hdmi0]-Sektion einfügen (nach hdmi_force_hotplug=1)
# Eine Sektion gilt nur bis zur nächsten [Sektion] – Optionen am Dateiende gelten sonst nicht für HDMI0
FIRST_HDMI0_SECTION=$(grep -A 8 "^\[hdmi0\]" "$CONFIG_FILE" | head -9)
if ! echo "$FIRST_HDMI0_SECTION" | grep -q "hdmi_edid_file=1"; then
  echo "  Füge hdmi_edid_file=1 in erste [hdmi0]-Sektion ein..."
  awk '/^\[hdmi0\]/{ inhdmi0=1; print; next }
       inhdmi0 && /^\[hdmi1\]/{ inhdmi0=0 }
       inhdmi0 && /^hdmi_force_hotplug=1$/ && !done{ print; print "hdmi_edid_file=1"; done=1; next }
       { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
  NEEDS_UPDATE=true
fi
FIRST_HDMI0_SECTION=$(grep -A 8 "^\[hdmi0\]" "$CONFIG_FILE" | head -9)
if ! echo "$FIRST_HDMI0_SECTION" | grep -q "hdmi_drive=2"; then
  echo "  Füge hdmi_drive=2 in erste [hdmi0]-Sektion ein..."
  awk '/^\[hdmi0\]/{ inhdmi0=1; print; next }
       inhdmi0 && /^\[hdmi1\]/{ inhdmi0=0 }
       inhdmi0 && /^hdmi_edid_file=1$/ && !done{ print; print "hdmi_drive=2"; done=1; next }
       { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
  if ! grep -A 8 "^\[hdmi0\]" "$CONFIG_FILE" | head -9 | grep -q "hdmi_drive=2"; then
    awk '/^\[hdmi0\]/{ inhdmi0=1; print; next }
         inhdmi0 && /^\[hdmi1\]/{ inhdmi0=0 }
         inhdmi0 && /^hdmi_force_hotplug=1$/ && !done{ print; print "hdmi_drive=2"; done=1; next }
         { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
  fi
  NEEDS_UPDATE=true
fi

if [ "$NEEDS_UPDATE" = true ]; then
  echo -e "  ${GREEN}✓${NC} config.txt aktualisiert"
else
  echo -e "  ${GREEN}✓${NC} config.txt bereits korrekt konfiguriert"
fi
echo ""

# 4. Zeige aktuelle Konfiguration
echo -e "${CYAN}[4] Aktuelle Konfiguration:${NC}"
echo "  [hdmi0] Sektion:"
grep -A 5 "^\[hdmi0\]" "$CONFIG_FILE" | grep -v "^--$" | sed 's/^/    /'
echo ""

# 5. Zusammenfassung
echo -e "${CYAN}[5] Zusammenfassung:${NC}"
echo ""
echo "Durchgeführte Änderungen:"
echo "  ✓ EDID-Datei vorhanden: $EDID_FILE"
echo "  ✓ config.txt konfiguriert:"
echo "    - hdmi_force_hotplug=1"
echo "    - hdmi_edid_file=1"
echo "    - hdmi_drive=2"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Neustart erforderlich!"
echo ""
echo "Nächste Schritte:"
echo "  1. Starte das System neu:"
echo "     sudo reboot"
echo ""
echo "  2. Nach dem Neustart prüfe:"
echo "     cat /sys/class/drm/card2-HDMI-A-1/enabled"
echo "     # Sollte 'enabled' sein"
echo ""
echo "  3. Aktiviere HDMI-A-1 Sink:"
echo "     ./scripts/activate-hdmi-a1-sink.sh"
echo ""
echo "  4. Teste Audio:"
echo "     ./scripts/test-freenove-speakers-simple.sh"
echo ""
echo -e "${YELLOW}Alternative:${NC} Falls nach Neustart immer noch kein Ton kommt,"
echo "teste ohne Monitor (Mediaboard könnte nur ohne Monitor funktionieren):"
echo "  - Monitor abstecken"
echo "  - ./scripts/test-freenove-speakers-simple.sh"
echo ""
echo -e "${GREEN}Fertig.${NC}"
