#!/bin/bash
#
# PI-Installer: NVMe + PCIe Diagnose
# Prüft:
# - Ob PCIe Gen3 in der Konfiguration aktivierbar/aktiviert ist
# - Aktuellen PCIe-Link (zur Laufzeit)
# - Ob NVMe erkannt und gemountet ist
# - Ob NVMe beim Booten gemountet werden soll (fstab/cmdline)
#

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

OK="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}!${NC}"

CONFIG_FILE="/boot/firmware/config.txt"
CMDLINE_FILE="/boot/firmware/cmdline.txt"

if [[ ! -f "$CONFIG_FILE" ]]; then
  CONFIG_FILE="/boot/config.txt"
fi

if [[ ! -f "$CMDLINE_FILE" ]]; then
  CMDLINE_FILE="/boot/cmdline.txt"
fi

echo -e "${CYAN}=== NVMe + PCIe Diagnose ===${NC}"
echo ""

echo -e "${CYAN}[1] PCIe-Konfiguration (Boot)${NC}"
if [[ -f "$CONFIG_FILE" ]]; then
  echo "  Datei: $CONFIG_FILE"
  gen_line=$(awk '
    /^[[:space:]]*#/ {next}
    /^[[:space:]]*dtparam=pciex1_gen=/ {line=$0}
    END {print line}
  ' "$CONFIG_FILE")

  if [[ -n "${gen_line:-}" ]]; then
    gen_value=$(echo "$gen_line" | sed -E 's/.*dtparam=pciex1_gen=([0-9]+).*/\1/')
    echo "  Aktiver Eintrag: $gen_line"
    if [[ "$gen_value" == "3" ]]; then
      echo -e "  $FAIL PCIe Gen3 ist in config.txt aktiviert."
    elif [[ "$gen_value" == "2" ]]; then
      echo -e "  $OK PCIe Gen3 ist deaktiviert (Gen2 gesetzt)."
    else
      echo -e "  $WARN Unbekannter Wert pciex1_gen=$gen_value"
    fi
  else
    echo -e "  $WARN Kein dtparam=pciex1_gen gesetzt (Firmware-Default aktiv)."
  fi
else
  echo -e "  $FAIL config.txt nicht gefunden."
fi
echo ""

echo -e "${CYAN}[2] PCIe-Link zur Laufzeit${NC}"
if command -v lspci >/dev/null 2>&1; then
  root_port=$(lspci -D | awk '/Broadcom.*BCM2712 PCIe Bridge/ {print $1; exit}')
  if [[ -n "${root_port:-}" ]]; then
    link_line=$(lspci -vv -s "$root_port" 2>/dev/null | awk '/LnkSta:/{print; exit}')
    target_line=$(lspci -vv -s "$root_port" 2>/dev/null | awk '/LnkCtl2:/{print; exit}')
    if [[ -n "${link_line:-}" ]]; then
      echo "  Root-Port: $root_port"
      echo "  $link_line"
      [[ -n "${target_line:-}" ]] && echo "  $target_line"

      if echo "$link_line" | grep -q "Speed 8GT/s"; then
        echo -e "  $FAIL Laufzeit-Link entspricht Gen3 (8GT/s)."
      elif echo "$link_line" | grep -q "Speed 5GT/s"; then
        echo -e "  $OK Laufzeit-Link entspricht Gen2 (5GT/s)."
      elif echo "$link_line" | grep -q "Speed 2.5GT/s"; then
        echo -e "  $WARN Laufzeit-Link nur Gen1 (2.5GT/s)."
      else
        echo -e "  $WARN Link-Geschwindigkeit konnte nicht eindeutig zugeordnet werden."
      fi
    else
      echo -e "  $WARN Keine Link-Informationen für Root-Port gefunden."
    fi
  else
    echo -e "  $WARN BCM2712 PCIe Root-Port nicht gefunden."
  fi
else
  echo -e "  $WARN lspci ist nicht installiert."
fi
echo ""

echo -e "${CYAN}[3] NVMe-Erkennung${NC}"
nvme_devices=()
while IFS= read -r dev; do
  [[ -n "$dev" ]] && nvme_devices+=("$dev")
done < <(ls /dev/nvme*n1 2>/dev/null || true)

if [[ ${#nvme_devices[@]} -eq 0 ]]; then
  echo -e "  $FAIL Keine NVMe-Blockdevices gefunden (/dev/nvme*n1)."
else
  echo -e "  $OK NVMe gefunden:"
  for dev in "${nvme_devices[@]}"; do
    size=$(lsblk -dn -o SIZE "$dev" 2>/dev/null || echo "?")
    model=$(lsblk -dn -o MODEL "$dev" 2>/dev/null | sed 's/[[:space:]]*$//' || echo "")
    echo "    - $dev  Größe: $size  Modell: ${model:-?}"
  done
fi
echo ""

echo -e "${CYAN}[4] NVMe-Mount-Status (aktuell)${NC}"
nvme_mounts=$(findmnt -rno SOURCE,TARGET,FSTYPE,OPTIONS | awk '$1 ~ /nvme/ {print}')
if [[ -n "${nvme_mounts:-}" ]]; then
  echo -e "  $OK Aktive NVMe-Mounts:"
  echo "$nvme_mounts" | while IFS= read -r line; do
    echo "    $line"
  done
else
  echo -e "  $WARN Keine aktiven NVMe-Mounts gefunden."
fi
echo ""

echo -e "${CYAN}[5] NVMe-Mount beim Boot (fstab + cmdline)${NC}"
if [[ -f /etc/fstab ]]; then
  fstab_nvme=$(awk '
    /^[[:space:]]*#/ {next}
    NF >= 2 && ($1 ~ /nvme/ || $2 ~ /nvme/) {print}
  ' /etc/fstab)
  if [[ -n "${fstab_nvme:-}" ]]; then
    echo -e "  $OK NVMe-Einträge in /etc/fstab:"
    echo "$fstab_nvme" | while IFS= read -r line; do
      echo "    $line"
    done
  else
    echo -e "  $WARN Keine NVMe-Einträge in /etc/fstab."
  fi
else
  echo -e "  $FAIL /etc/fstab nicht gefunden."
fi

if [[ -f "$CMDLINE_FILE" ]]; then
  root_spec=$(sed -nE 's/.*\b(root=[^ ]+).*/\1/p' "$CMDLINE_FILE")
  if [[ -n "${root_spec:-}" ]]; then
    echo "  cmdline root: $root_spec"
    if echo "$root_spec" | grep -q "nvme"; then
      echo -e "  $OK Root in cmdline zeigt auf NVMe."
    else
      echo -e "  $WARN Root in cmdline zeigt nicht auf NVMe."
    fi
  else
    echo -e "  $WARN Kein root=... in cmdline gefunden."
  fi
else
  echo -e "  $FAIL cmdline.txt nicht gefunden."
fi
echo ""

echo -e "${CYAN}[6] Kurzfazit${NC}"
root_now=$(findmnt -n -o SOURCE / 2>/dev/null || true)
boot_now=$(findmnt -n -o SOURCE /boot/firmware 2>/dev/null || true)
echo "  Aktuelles Root: ${root_now:-?}"
echo "  Aktuelles Boot: ${boot_now:-?}"
echo ""
echo -e "${CYAN}=== Ende Diagnose ===${NC}"
