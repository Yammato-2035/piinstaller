#!/bin/bash
# PI-Installer: EDID für HDMI-A-1 per Kernel (drm.edid_firmware) erzwingen
#
# Auf Pi 5 + Bookworm wird hdmi_edid_file in config.txt oft ignoriert.
# Alternative: EDID nach /lib/firmware legen und in cmdline.txt
# drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin setzen.
#
# Siehe: docs/WHY_EDID_CANNOT_BE_FORCED.md
#
# Ausführung: sudo ./scripts/fix-edid-via-kernel-cmdline.sh

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

echo -e "${CYAN}=== EDID für HDMI-A-1 per Kernel (drm.edid_firmware) ===${NC}"
echo ""

BOOT_EDID="/boot/firmware/edid.dat"
LIB_EDID="/lib/firmware/edid-hdmi-a1.bin"
CMDLINE="/boot/firmware/cmdline.txt"
PARAM="drm.edid_firmware=HDMI-A-1:edid-hdmi-a1.bin"

# 1. EDID-Quelle
if [ ! -f "$BOOT_EDID" ]; then
  if [ -f "/sys/class/drm/card2-HDMI-A-2/edid" ]; then
    echo "  Kopiere EDID von HDMI-A-2 nach $BOOT_EDID..."
    cp /sys/class/drm/card2-HDMI-A-2/edid "$BOOT_EDID"
  else
    echo -e "  ${RED}✗${NC} Keine EDID-Quelle (weder $BOOT_EDID noch HDMI-A-2)"
    exit 1
  fi
fi

# 2. Nach /lib/firmware kopieren
echo "  Kopiere EDID nach $LIB_EDID..."
cp "$BOOT_EDID" "$LIB_EDID"
echo -e "  ${GREEN}✓${NC} $LIB_EDID"
echo ""

# 3. cmdline.txt anpassen
if grep -q "drm.edid_firmware" "$CMDLINE" 2>/dev/null; then
  echo "  drm.edid_firmware bereits in cmdline.txt"
  grep "drm.edid_firmware" "$CMDLINE" | sed 's/^/    /'
else
  echo "  Füge $PARAM zu cmdline.txt hinzu..."
  # cmdline.txt ist eine Zeile
  sed -i "s/$/ $PARAM/" "$CMDLINE"
  echo -e "  ${GREEN}✓${NC} cmdline.txt aktualisiert"
fi
echo ""

echo -e "${YELLOW}Neustart erforderlich.${NC}"
echo "Nach dem Neustart prüfen:"
echo "  dmesg | grep -i edid"
echo "  cat /sys/class/drm/card2-HDMI-A-1/enabled"
echo ""
echo -e "${GREEN}Fertig.${NC}"
