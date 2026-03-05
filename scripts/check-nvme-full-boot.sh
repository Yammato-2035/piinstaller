#!/bin/bash
#
# check-nvme-full-boot.sh
# Prüft die NVMe und deren Partitionen für den Pi-5-Vollboot:
# - Wird die NVMe erkannt?
# - Sind Boot- (FAT) und Root-Partition (ext4) vorhanden?
# - Enthält die Boot-Partition config.txt, cmdline.txt, Kernel?
# - Enthält die Root-Partition /etc, /bin (System)?
# - EEPROM Boot-Reihenfolge
#
# Mit oder ohne sudo ausführbar (Mount nur mit sudo).
# Siehe: docs/NVME_FULL_BOOT.md
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

OK="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}!${NC}"

can_mount=false
[[ $EUID -eq 0 ]] && can_mount=true

echo -e "${CYAN}=== NVMe-Vollboot – Diagnose ===${NC}"
echo ""

# 1. Raspberry Pi 5
echo -e "${CYAN}[1] Raspberry Pi${NC}"
if [[ -f /proc/device-tree/model ]]; then
  MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)
  echo -e "  $OK Modell: $MODEL"
  if [[ "$MODEL" != *"Raspberry Pi 5"* ]]; then
    echo -e "  ${WARN} Vollboot von NVMe ist für Pi 5 ausgelegt."
  fi
else
  echo -e "  $FAIL /proc/device-tree/model nicht gefunden (kein Pi?)"
fi
echo ""

# 2. NVMe-Blockgeräte
echo -e "${CYAN}[2] NVMe-Blockgeräte${NC}"
NVME_DEVS=()
while read -r dev; do
  [[ -n "$dev" ]] && NVME_DEVS+=("$dev")
done < <(lsblk -d -n -o NAME,TRAN 2>/dev/null | awk '$2=="nvme" {print "/dev/"$1}')

if [[ ${#NVME_DEVS[@]} -eq 0 ]]; then
  echo -e "  $FAIL Keine NVMe gefunden (lsblk -d -n -o NAME,TRAN)."
  echo -e "  Prüfen: PCIe-HAT/Adapter, Kabel, dmesg | tail -20"
  exit 1
fi

for dev in "${NVME_DEVS[@]}"; do
  echo -e "  $OK $dev"
  if [[ -b "$dev" ]]; then
    size=$(lsblk -d -n -o SIZE "$dev" 2>/dev/null | tr -d ' ')
    echo -e "      Größe: $size"
  fi
done
echo ""

# 3. Partitionstabelle pro NVMe
for NVME_DEV in "${NVME_DEVS[@]}"; do
  echo -e "${CYAN}[3] Partitionen: $NVME_DEV${NC}"
  if ! [[ -b "$NVME_DEV" ]]; then
    echo -e "  $FAIL Gerät nicht vorhanden."
    echo ""
    continue
  fi

  fdisk -l "$NVME_DEV" 2>/dev/null || true
  echo ""

  P1="${NVME_DEV}p1"
  P2="${NVME_DEV}p2"

  has_p1=false
  has_p2=false
  [[ -b "$P1" ]] && has_p1=true
  [[ -b "$P2" ]] && has_p2=true

  if $has_p1; then
    echo -e "  $OK $P1 vorhanden"
    p1_type=$(lsblk -n -o FSTYPE "$P1" 2>/dev/null || true)
    p1_size=$(lsblk -n -o SIZE "$P1" 2>/dev/null | tr -d ' ')
    echo -e "      FSTYPE: ${p1_type:-?}  Größe: $p1_size"
  else
    echo -e "  $FAIL $P1 fehlt (Boot-Partition erwartet: FAT32, ~256 MiB)"
  fi

  if $has_p2; then
    echo -e "  $OK $P2 vorhanden"
    p2_type=$(lsblk -n -o FSTYPE "$P2" 2>/dev/null || true)
    p2_size=$(lsblk -n -o SIZE "$P2" 2>/dev/null | tr -d ' ')
    echo -e "      FSTYPE: ${p2_type:-?}  Größe: $p2_size"
  else
    echo -e "  $FAIL $P2 fehlt (Root-Partition erwartet: ext4)"
  fi
  echo ""

  # 4. Inhalt Boot-Partition (nur mit sudo)
  if $has_p1 && $can_mount; then
    echo -e "${CYAN}[4] Inhalt Boot-Partition ($P1)${NC}"
    MNT=$(mktemp -d)
    if mount -o ro "$P1" "$MNT" 2>/dev/null; then
      for f in config.txt cmdline.txt; do
        if [[ -f "$MNT/$f" ]]; then
          echo -e "  $OK $f vorhanden"
          if [[ "$f" == "cmdline.txt" ]]; then
            root_val=$(grep -o 'root=[^ ]*' "$MNT/$f" 2>/dev/null || true)
            echo -e "      $root_val"
          fi
        else
          echo -e "  $FAIL $f fehlt (für Boot erforderlich)"
        fi
      done
      kernels=("$MNT"/kernel*.img "$MNT"/Image)
      found_kernel=false
      for k in "${kernels[@]}"; do
        [[ -f $k ]] && found_kernel=true && echo -e "  $OK Kernel: $(basename "$k")" && break
      done
      $found_kernel || echo -e "  $WARN Kein Kernel (kernel*.img / Image) gefunden"
      umount "$MNT" 2>/dev/null || true
    else
      echo -e "  $FAIL Mount von $P1 fehlgeschlagen (Dateisystem kaputt oder kein FAT?)"
    fi
    rmdir "$MNT" 2>/dev/null || true
    echo ""
  elif $has_p1 && ! $can_mount; then
    echo -e "${CYAN}[4] Inhalt Boot-Partition${NC}"
    echo -e "  $WARN Bitte mit sudo ausführen, um Boot-Inhalt zu prüfen: sudo $0"
    echo ""
  fi

  # 5. Inhalt Root-Partition (nur mit sudo)
  if $has_p2 && $can_mount; then
    echo -e "${CYAN}[5] Inhalt Root-Partition ($P2)${NC}"
    MNT=$(mktemp -d)
    if mount -o ro "$P2" "$MNT" 2>/dev/null; then
      for d in etc bin usr; do
        if [[ -d "$MNT/$d" ]]; then
          echo -e "  $OK /$d vorhanden"
        else
          echo -e "  $FAIL /$d fehlt (kein vollständiges Root?)"
        fi
      done
      if [[ -f "$MNT/etc/fstab" ]]; then
        echo -e "  $OK /etc/fstab vorhanden"
        grep -E '^[^#]*[[:space:]]/[[:space:]]' "$MNT/etc/fstab" 2>/dev/null | head -1 || true
      else
        echo -e "  $FAIL /etc/fstab fehlt"
      fi
      umount "$MNT" 2>/dev/null || true
    else
      echo -e "  $FAIL Mount von $P2 fehlgeschlagen (Dateisystem kaputt oder kein ext4?)"
    fi
    rmdir "$MNT" 2>/dev/null || true
    echo ""
  elif $has_p2 && ! $can_mount; then
    echo -e "${CYAN}[5] Inhalt Root-Partition${NC}"
    echo -e "  $WARN Bitte mit sudo ausführen, um Root-Inhalt zu prüfen: sudo $0"
    echo ""
  fi
done

# 6. EEPROM Boot-Reihenfolge
echo -e "${CYAN}[6] EEPROM Boot-Reihenfolge${NC}"
if command -v rpi-eeprom-config >/dev/null 2>&1; then
  boot_order=$(rpi-eeprom-config 2>/dev/null | grep -E '^BOOT_ORDER=' || true)
  if [[ -n "$boot_order" ]]; then
    echo -e "  $OK $boot_order"
    if [[ "$boot_order" != *"0xf146"* ]]; then
      echo -e "  $WARN Für NVMe zuerst: BOOT_ORDER=0xf146 setzen (sudo -E rpi-eeprom-config --edit)"
    fi
  else
    echo -e "  $WARN BOOT_ORDER nicht gefunden (Standard: oft SD zuerst)"
    echo -e "      NVMe zuerst: sudo -E rpi-eeprom-config --edit → BOOT_ORDER=0xf146"
  fi
else
  echo -e "  $WARN rpi-eeprom-config nicht gefunden (nur auf dem Pi)"
fi
echo ""

# 7. Aktuelles Root
echo -e "${CYAN}[7] Aktuelles System (von wo booten Sie gerade?)${NC}"
ROOT_DEV=$(findmnt -n -o SOURCE / 2>/dev/null || true)
BOOT_DEV=$(findmnt -n -o SOURCE /boot/firmware 2>/dev/null || true)
echo -e "  Root:  ${ROOT_DEV:-?}"
echo -e "  Boot:  ${BOOT_DEV:-?}"
if [[ "$ROOT_DEV" == *"nvme"* ]] && [[ "$BOOT_DEV" == *"nvme"* ]]; then
  echo -e "  $OK Sie booten bereits von der NVMe."
elif [[ "$ROOT_DEV" == *"nvme"* ]]; then
  echo -e "  $WARN Hybrid: Root von NVMe, Boot von SD. Für Vollboot siehe docs/NVME_FULL_BOOT.md"
else
  echo -e "  $WARN Sie booten von SD (oder anderem). NVMe ist nur Datenträger."
fi
echo ""

echo -e "${CYAN}=== Ende Diagnose ===${NC}"
echo "Wenn die NVMe leer ist oder Partitionen fehlen:"
echo "  • Setup erneut ausführen: sudo ./scripts/setup-nvme-full-boot.sh"
echo "  • Siehe: docs/NVME_FULL_BOOT.md"
