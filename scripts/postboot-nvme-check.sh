#!/bin/bash
#
# PI-Installer: Postboot NVMe/PCIe Check
# Einmal ausfuehren nach Neustart:
#   sudo ./scripts/postboot-nvme-check.sh
#

set -u

TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="/home/gabrielglienke/Documents/PI-Installer/logs"
OUT_FILE="$OUT_DIR/nvme-postboot-check-$TS.log"

mkdir -p "$OUT_DIR"

exec > >(tee "$OUT_FILE") 2>&1

echo "=== NVMe Postboot Check ==="
echo "Zeit: $(date -Iseconds)"
echo ""

echo "[1] Basis"
echo "Host: $(hostname)"
echo "Kernel: $(uname -r)"
if [[ -f /proc/device-tree/model ]]; then
  echo "Modell: $(tr -d '\0' < /proc/device-tree/model)"
fi
echo ""

echo "[2] Boot-Konfiguration (relevant)"
CONFIG_FILE="/boot/firmware/config.txt"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
[[ -f "$CONFIG_FILE" ]] || CONFIG_FILE="/boot/config.txt"
[[ -f "$CMDLINE_FILE" ]] || CMDLINE_FILE="/boot/cmdline.txt"

echo "config: $CONFIG_FILE"
awk '
  /^[[:space:]]*#/ {next}
  /dtparam=pciex1_gen=/ || /pcie/ || /nvme/ {print}
' "$CONFIG_FILE" 2>/dev/null || true

echo ""
echo "cmdline: $CMDLINE_FILE"
cat "$CMDLINE_FILE" 2>/dev/null || true
echo ""

echo "[3] PCIe / NVMe Enumeration"
lspci -nn 2>/dev/null | awk '
  /PCI bridge/ || /Non-Volatile memory controller/ || /NVMe/ || /BCM2712 PCIe Bridge/ {print}
' || true
echo ""

ROOT_PORT="$(lspci -D 2>/dev/null | awk '/Broadcom.*BCM2712 PCIe Bridge/ {print $1; exit}')"
if [[ -n "${ROOT_PORT:-}" ]]; then
  echo "Root-Port: $ROOT_PORT"
  lspci -vv -s "$ROOT_PORT" 2>/dev/null | awk '/LnkCap:|LnkSta:|LnkCtl2:/{print}'
fi
echo ""

echo "[4] Blockdevices / NVMe Nodes"
lsblk -o NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS,SIZE,MODEL 2>/dev/null || true
echo ""
ls /dev/nvme* 2>/dev/null || echo "Keine /dev/nvme* Nodes."
echo ""
nvme list 2>/dev/null || true
echo ""

echo "[5] Mounts / Boot-Mount-Konfig"
echo "Aktive NVMe-Mounts:"
findmnt -rno SOURCE,TARGET,FSTYPE,OPTIONS 2>/dev/null | awk '$1 ~ /nvme/ {print}' || true
echo ""
echo "fstab NVMe-Zeilen:"
awk '
  /^[[:space:]]*#/ {next}
  $0 ~ /nvme/ {print}
' /etc/fstab 2>/dev/null || true
echo ""

echo "[6] Kernel-Log (NVMe/PCIe, letzte 200)"
journalctl -k -n 200 --no-pager 2>/dev/null | awk '
  BEGIN { IGNORECASE=1 }
  /nvme|pcie|aer|link down|link up|timeout|reset|cannot be assigned|subordinate/ {print}
' || true
echo ""

echo "[7] Schnellfazit"
if ls /dev/nvme*n1 >/dev/null 2>&1; then
  echo "OK: NVMe-Blockdevice vorhanden."
else
  echo "WARN: Kein NVMe-Blockdevice vorhanden."
fi

if findmnt -rno SOURCE / 2>/dev/null | grep -q nvme; then
  echo "OK: Root laeuft auf NVMe."
else
  echo "INFO: Root laeuft nicht auf NVMe."
fi

if grep -q "dtparam=pciex1_gen=2" "$CONFIG_FILE" 2>/dev/null; then
  echo "OK: PCIe Gen3 ist deaktiviert (Gen2 konfiguriert)."
fi

echo ""
echo "Log gespeichert unter: $OUT_FILE"
