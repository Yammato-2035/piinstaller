#!/usr/bin/env bash
# PI-Installer – Freenove Computer Case: Bildschirmrotation setzen
# Setzt display_rotate in /boot/firmware/config.txt (oder /boot/config.txt).
# Nach Änderung Neustart: sudo reboot
#
# Verwendung auf dem Raspberry Pi:
#   sudo ./freenove-set-display-rotate.sh [0|90|180|270]
#   sudo ./freenove-set-display-rotate.sh    # fragt interaktiv ab
#
# Werte: 0=Normal, 90=90° CW, 180=180°, 270=270° (90° CCW)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

CONFIG_FILE="/boot/firmware/config.txt"
CONFIG_LEGACY="/boot/config.txt"

usage() {
  echo "Verwendung: sudo $0 [0|90|180|270]"
  echo ""
  echo "  Setzt die Bildschirmrotation für das Freenove-Display (config.txt)."
  echo "  Nach der Änderung Neustart: sudo reboot"
  echo ""
  echo "  Werte: 0=Normal, 90=90° im Uhrzeigersinn, 180=180°, 270=270° (90° gegen Uhrzeigersinn)"
  exit 1
}

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Fehler: Bitte mit sudo ausführen: sudo $0 [0|90|180|270]${NC}"
  exit 1
fi

[ -f "$CONFIG_FILE" ] || CONFIG_FILE="$CONFIG_LEGACY"
if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "${RED}Fehler: config.txt nicht gefunden (weder /boot/firmware/config.txt noch /boot/config.txt)${NC}"
  exit 1
fi

# Argument: 0, 90, 180, 270 → config-Wert 0, 1, 2, 3
if [ -n "$1" ]; then
  case "$1" in
    0)   ROTATE_VAL=0 ;;
    90)  ROTATE_VAL=1 ;;
    180) ROTATE_VAL=2 ;;
    270) ROTATE_VAL=3 ;;
    *)   echo -e "${RED}Ungültiger Winkel. Erlaubt: 0, 90, 180, 270${NC}"; usage ;;
  esac
else
  echo -e "${CYAN}Bildschirmrotation für Freenove-Display${NC}"
  echo "  0  = Normal (0°)"
  echo "  90 = 90° im Uhrzeigersinn (Case steht, Display war seitlich)"
  echo "  180 = 180°"
  echo "  270 = 90° gegen Uhrzeigersinn"
  echo ""
  read -r -p "Winkel [0|90|180|270]: " INPUT
  case "$INPUT" in
    0)   ROTATE_VAL=0 ;;
    90)  ROTATE_VAL=1 ;;
    180) ROTATE_VAL=2 ;;
    270) ROTATE_VAL=3 ;;
    *)   echo -e "${RED}Ungültig. Erlaubt: 0, 90, 180, 270${NC}"; exit 1 ;;
  esac
fi

BACKUP_DIR="$(dirname "$CONFIG_FILE")"
TS="$(date +%Y%m%d-%H%M%S)"
cp -a "$CONFIG_FILE" "${CONFIG_FILE}.backup.${TS}"
echo -e "${GREEN}Backup: ${CONFIG_FILE}.backup.${TS}${NC}"

# Bestehende display_rotate-Zeile entfernen, neue anhängen
if grep -q '^display_rotate=' "$CONFIG_FILE"; then
  sed -i '/^display_rotate=/d' "$CONFIG_FILE"
fi
echo "display_rotate=$ROTATE_VAL" >> "$CONFIG_FILE"
echo -e "${GREEN}display_rotate=$ROTATE_VAL gesetzt.${NC}"
echo ""
echo "Neustart ausführen, damit die Änderung wirkt: sudo reboot"
