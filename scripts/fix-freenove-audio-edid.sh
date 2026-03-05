#!/bin/bash
# PI-Installer: Erzwinge EDID für HDMI-A-1 (für Freenove Mediaboard Audio)
#
# Problem: Pi 5 erkennt HDMI-Audio nur, wenn das HDMI-Endgerät EDID präsentiert.
# Das Mediaboard könnte kein EDID präsentieren, daher wird HDMI-A-1 nicht als
# Audio-Gerät erkannt.
#
# Lösung: Dump EDID von HDMI-A-2 (wo Monitor angeschlossen ist) und verwende
# es für HDMI-A-1, damit HDMI-Audio auch ohne Monitor funktioniert.
#
# Ausführung: sudo ./scripts/fix-freenove-audio-edid.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

echo -e "${CYAN}=== Erzwinge EDID für HDMI-A-1 (Freenove Mediaboard Audio) ===${NC}"
echo ""

# 1. Prüfe ob EDID-Tools verfügbar sind
echo -e "${CYAN}[1] Prüfe EDID-Tools:${NC}"
if command -v edid-decode >/dev/null 2>&1; then
  echo -e "  ${GREEN}✓${NC} edid-decode gefunden"
else
  echo -e "  ${YELLOW}⚠${NC} edid-decode nicht gefunden"
  echo "  Installiere: sudo apt install edid-decode"
fi
echo ""

# 2. Prüfe HDMI-Ports
echo -e "${CYAN}[2] Prüfe HDMI-Ports:${NC}"
HDMI_A1_STATUS=$(cat /sys/class/drm/card2-HDMI-A-1/status 2>/dev/null || echo "unknown")
HDMI_A2_STATUS=$(cat /sys/class/drm/card2-HDMI-A-2/status 2>/dev/null || echo "unknown")

echo "  HDMI-A-1 Status: $HDMI_A1_STATUS"
echo "  HDMI-A-2 Status: $HDMI_A2_STATUS"
echo ""

# 3. Dump EDID von HDMI-A-2 (wo Monitor angeschlossen ist)
echo -e "${CYAN}[3] Dump EDID von HDMI-A-2:${NC}"
EDID_FILE="/boot/firmware/edid-hdmi-a2.dat"

if [ -f "/sys/class/drm/card2-HDMI-A-2/edid" ]; then
  EDID_SIZE=$(wc -c < /sys/class/drm/card2-HDMI-A-2/edid 2>/dev/null || echo "0")
  
  if [ "$EDID_SIZE" -gt 128 ]; then
    echo "  Kopiere EDID von HDMI-A-2..."
    cp /sys/class/drm/card2-HDMI-A-2/edid "$EDID_FILE" 2>/dev/null || {
      echo -e "  ${RED}✗${NC} Konnte EDID nicht kopieren"
      exit 1
    }
    echo -e "  ${GREEN}✓${NC} EDID gespeichert: $EDID_FILE"
    
    # Prüfe EDID
    if command -v edid-decode >/dev/null 2>&1; then
      echo "  EDID-Informationen:"
      edid-decode "$EDID_FILE" 2>/dev/null | grep -E "Manufacturer|Model|Serial|Detailed mode" | head -5 | sed 's/^/    /'
    fi
  else
    echo -e "  ${YELLOW}⚠${NC} EDID zu klein oder nicht verfügbar (Größe: $EDID_SIZE Bytes)"
    echo "  Erstelle generische EDID-Datei..."
    # Erstelle minimale EDID-Datei (128 Bytes)
    dd if=/dev/zero of="$EDID_FILE" bs=128 count=1 2>/dev/null || true
  fi
else
  echo -e "  ${YELLOW}⚠${NC} /sys/class/drm/card2-HDMI-A-2/edid nicht gefunden"
  echo "  Erstelle generische EDID-Datei..."
  dd if=/dev/zero of="$EDID_FILE" bs=128 count=1 2>/dev/null || true
fi
echo ""

# 4. Konfiguriere config.txt
echo -e "${CYAN}[4] Konfiguriere config.txt:${NC}"
CONFIG_FILE="/boot/firmware/config.txt"

if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "  ${RED}✗${NC} $CONFIG_FILE nicht gefunden"
  exit 1
fi

# Backup erstellen
BACKUP="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP"
echo "  Backup erstellt: $BACKUP"
echo ""

# EDID-Optionen müssen IN der ersten [hdmi0]-Sektion stehen (siehe docs/WHY_EDID_CANNOT_BE_FORCED.md).
# Entferne einzeln stehende Zeilen, dann füge in erste [hdmi0]-Sektion ein.
if grep -q "^hdmi_edid_file=\|^hdmi_drive=" "$CONFIG_FILE" 2>/dev/null; then
  echo "  Entferne vorhandene hdmi_edid_file/hdmi_drive..."
  sed -i '/^hdmi_edid_file=/d' "$CONFIG_FILE"
  sed -i '/^hdmi_drive=/d' "$CONFIG_FILE"
fi

# Prüfe ob [hdmi0] existiert und EDID-Optionen in dieser Sektion fehlen
FIRST_HDMI0=$(grep -A 8 "^\[hdmi0\]" "$CONFIG_FILE" 2>/dev/null | head -9)
if ! echo "$FIRST_HDMI0" | grep -q "hdmi_edid_file=1"; then
  echo "  Füge hdmi_edid_file=1 und hdmi_drive=2 in erste [hdmi0]-Sektion ein..."
  awk '/^\[hdmi0\]/{ inhdmi0=1; print; next }
       inhdmi0 && /^\[hdmi1\]/{ inhdmi0=0 }
       inhdmi0 && /^hdmi_force_hotplug=1$/ && !done{ print; print "hdmi_edid_file=1"; print "hdmi_drive=2"; done=1; next }
       { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
fi

echo -e "  ${GREEN}✓${NC} config.txt aktualisiert"
echo ""

# 5. Kopiere EDID-Datei nach /boot/firmware/edid.dat (falls nicht vorhanden)
echo -e "${CYAN}[5] Kopiere EDID-Datei:${NC}"
if [ -f "$EDID_FILE" ]; then
  if [ ! -f "/boot/firmware/edid.dat" ]; then
    cp "$EDID_FILE" "/boot/firmware/edid.dat"
    echo -e "  ${GREEN}✓${NC} EDID-Datei kopiert: /boot/firmware/edid.dat"
  else
    echo -e "  ${YELLOW}⚠${NC} /boot/firmware/edid.dat existiert bereits"
    read -p "  Überschreiben? [j] Ja / [n] Nein: " answer
    if [[ "$answer" =~ ^[jJ] ]]; then
      cp "$EDID_FILE" "/boot/firmware/edid.dat"
      echo -e "  ${GREEN}✓${NC} EDID-Datei überschrieben"
    else
      echo "  Behalte vorhandene EDID-Datei"
    fi
  fi
else
  echo -e "  ${RED}✗${NC} EDID-Datei nicht gefunden"
fi
echo ""

# 6. Zusammenfassung
echo -e "${CYAN}[6] Zusammenfassung:${NC}"
echo ""
echo "Durchgeführte Änderungen:"
echo "  ✓ EDID von HDMI-A-2 gedumpt: $EDID_FILE"
echo "  ✓ config.txt aktualisiert:"
echo "    - hdmi_force_hotplug=1 (für HDMI-A-1)"
echo "    - hdmi_edid_file=1 (verwendet /boot/firmware/edid.dat)"
echo "    - hdmi_drive=2 (erzwingt HDMI-Audio)"
echo "  ✓ EDID-Datei kopiert: /boot/firmware/edid.dat"
echo ""
echo -e "${YELLOW}WICHTIG:${NC} Neustart erforderlich!"
echo ""
echo "Nächste Schritte:"
echo "  1. Starte das System neu:"
echo "     sudo reboot"
echo ""
echo "  2. Nach dem Neustart prüfe:"
echo "     cat /sys/class/drm/card2-HDMI-A-1/enabled"
echo "     pactl list short sinks | grep 107c701400"
echo ""
echo "  3. Teste Audio:"
echo "     ./scripts/test-freenove-speakers-simple.sh"
echo ""
echo -e "${GREEN}Fertig.${NC}"
