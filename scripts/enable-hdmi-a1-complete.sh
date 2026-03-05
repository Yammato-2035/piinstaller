#!/bin/bash
# PI-Installer: HDMI-A-1 vollständig aktivieren (Freenove Mediaboard Audio)
#
# Problem: HDMI-A-1 bleibt "disabled", kein Ton aus Gehäuselautsprechern.
# Pi 5 + Bookworm: config.txt-EDID wird oft ignoriert. Lösung: cmdline.txt
# mit video=HDMI-A-1:e UND drm.edid_firmware, plus EDID in /lib/firmware.
#
# Ausführung: sudo ./scripts/enable-hdmi-a1-complete.sh

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

echo -e "${CYAN}=== HDMI-A-1 vollständig aktivieren (Freenove Mediaboard) ===${NC}"
echo ""

CMDLINE="/boot/firmware/cmdline.txt"
CONFIG_FILE="/boot/firmware/config.txt"
BOOT_EDID="/boot/firmware/edid.dat"
LIB_EDID="/lib/firmware/edid-hdmi-a1.bin"

# --- 1. cmdline.txt: video=HDMI-A-1:e (erzwingt Port bei Boot) ---
echo -e "${CYAN}[1] cmdline.txt: video=HDMI-A-1:e${NC}"
if [ ! -f "$CMDLINE" ]; then
  echo -e "  ${RED}✗${NC} $CMDLINE nicht gefunden"
  exit 1
fi

CURRENT=$(cat "$CMDLINE" | tr -d '\n')
BACKUP="$CMDLINE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CMDLINE" "$BACKUP"
echo "  Backup: $BACKUP"

# Entferne alte video=HDMI- und drm.edid_firmware-Einträge
CURRENT=$(echo "$CURRENT" | sed 's/video=HDMI[^ ]*//g' | sed 's/drm\.edid_firmware=[^ ]*//g' | sed 's/  */ /g' | sed 's/^ //;s/ $//')

# Füge video=HDMI-A-1:e hinzu (Kernel aktiviert Port)
if echo "$CURRENT" | grep -q "video=HDMI-A-1"; then
  echo -e "  ${GREEN}✓${NC} video=HDMI-A-1 bereits vorhanden"
else
  CURRENT="$CURRENT video=HDMI-A-1:e"
  echo -e "  ${GREEN}✓${NC} video=HDMI-A-1:e hinzugefügt"
fi

# --- 2. EDID für HDMI-A-1 (Kernel lädt aus /lib/firmware) ---
echo ""
echo -e "${CYAN}[2] EDID für HDMI-A-1 (drm.edid_firmware)${NC}"
if [ ! -f "$BOOT_EDID" ] && [ -f "/sys/class/drm/card2-HDMI-A-2/edid" ]; then
  echo "  Kopiere EDID von HDMI-A-2 nach $BOOT_EDID..."
  cp /sys/class/drm/card2-HDMI-A-2/edid "$BOOT_EDID"
fi
if [ -f "$BOOT_EDID" ]; then
  cp "$BOOT_EDID" "$LIB_EDID"
  echo -e "  ${GREEN}✓${NC} $LIB_EDID"
  if ! echo "$CURRENT" | grep -q "drm.edid_firmware"; then
    CURRENT="$CURRENT drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin"
    echo -e "  ${GREEN}✓${NC} drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin in cmdline"
  else
    echo -e "  ${GREEN}✓${NC} drm.edid_firmware bereits in cmdline"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} Keine EDID-Datei (Monitor an HDMI-A-2 für Dump nötig)"
fi

echo "$CURRENT" > "$CMDLINE"
echo ""

# --- 3. config.txt: [hdmi0] mit hdmi_force_hotplug, hdmi_edid_file, hdmi_drive ---
echo -e "${CYAN}[3] config.txt: [hdmi0]-Sektion${NC}"
if [ -f "$CONFIG_FILE" ]; then
  # Entferne einzeln stehende Zeilen
  sed -i '/^hdmi_edid_file=/d' "$CONFIG_FILE"
  sed -i '/^hdmi_drive=/d' "$CONFIG_FILE"
  # In erste [hdmi0]-Sektion einfügen, falls fehlend
  FIRST=$(grep -A 8 "^\[hdmi0\]" "$CONFIG_FILE" 2>/dev/null | head -9)
  if ! echo "$FIRST" | grep -q "hdmi_edid_file=1"; then
    awk '/^\[hdmi0\]/{ inhdmi0=1; print; next }
         inhdmi0 && /^\[hdmi1\]/{ inhdmi0=0 }
         inhdmi0 && /^hdmi_force_hotplug=1$/ && !done{ print; print "hdmi_edid_file=1"; print "hdmi_drive=2"; done=1; next }
         { print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    echo -e "  ${GREEN}✓${NC} hdmi_edid_file=1, hdmi_drive=2 in [hdmi0]"
  else
    echo -e "  ${GREEN}✓${NC} [hdmi0] bereits mit EDID-Optionen"
  fi
else
  echo -e "  ${YELLOW}⚠${NC} $CONFIG_FILE nicht gefunden"
fi
echo ""

# --- 4. Ausgabe ---
echo -e "${CYAN}[4] Aktuelle cmdline.txt (relevant):${NC}"
grep -o 'video=HDMI[^ ]*\|drm.edid_firmware=[^ ]*' "$CMDLINE" 2>/dev/null | sed 's/^/  /' || echo "  (keine)"
echo ""
echo -e "${YELLOW}Neustart erforderlich.${NC}"
echo ""
echo "Nach dem Neustart:"
echo "  1. Prüfen: cat /sys/class/drm/card2-HDMI-A-1/enabled  # sollte 'enabled' sein"
echo "  2. Unter X11 (wichtig):"
echo "     ./scripts/fix-x11-hdmi-a1-deactivation.sh"
echo "     Danach abmelden und wieder anmelden (oder erneut reboot),"
echo "     sonst schaltet .xprofile HDMI-A-1 wieder aus."
echo "  3. Sink aktivieren: ./scripts/activate-hdmi-a1-sink.sh"
echo "  4. Test: ./scripts/test-freenove-speakers-simple.sh"
echo ""
echo -e "${GREEN}Fertig.${NC} Bitte Neustart: sudo reboot"
