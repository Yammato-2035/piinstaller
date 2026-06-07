#!/usr/bin/env bash
# Read-only verification of FAT32 ESP Rescue USB layout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
EXPECTED_FAT_LABEL="$(python3 - <<'PY'
from core.rescue_fat32_esp_usb_writer import FAT_VOLUME_LABEL
print(FAT_VOLUME_LABEL)
PY
)"
EXPECTED_GPT_PART_NAME="$(python3 - <<'PY'
from core.rescue_fat32_esp_usb_writer import GPT_PARTITION_NAME
print(GPT_PARTITION_NAME)
PY
)"
EFI_PARTTYPE_UUID="c12a7328-f81f-11d2-ba4b-00a0c93ec93b"

TARGET=""
PART=""
MOUNT=""
usage() {
  echo "Usage: $0 --target /dev/sdX [--partition /dev/sdX1]" >&2
  exit 20
}

fail() {
  echo "RESCUE-FAT32-VERIFY: $1" >&2
  exit "${2:-1}"
}

read_fat_volume_label() {
  local dev="$1"
  local label=""
  label="$(blkid -p -s LABEL -o value "$dev" 2>/dev/null | head -1 || true)"
  if [[ -n "$label" ]]; then
    echo "$label"
    return 0
  fi
  if command -v fatlabel >/dev/null 2>&1; then
    label="$(fatlabel "$dev" 2>/dev/null | head -1 || true)"
    [[ -n "$label" ]] && echo "$label" && return 0
  fi
  if command -v dosfslabel >/dev/null 2>&1; then
    label="$(dosfslabel "$dev" 2>/dev/null | head -1 || true)"
    [[ -n "$label" ]] && echo "$label" && return 0
  fi
  echo ""
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --partition) PART="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$TARGET" ]] || usage
[[ "$TARGET" != /dev/sda ]] || fail "forbidden target /dev/sda" 27
[[ "$TARGET" != /dev/nvme* ]] || fail "forbidden nvme target" 27

if [[ -z "$PART" ]]; then
  PART="${TARGET}1"
fi

sudo udevadm settle --timeout=15 2>/dev/null || udevadm settle --timeout=15 2>/dev/null || true

# GPT check
PTTYPE="$(lsblk -no PTTYPE "$TARGET" 2>/dev/null | head -1 || true)"
[[ "$PTTYPE" == "gpt" ]] || fail "no GPT on target (PTTYPE=${PTTYPE:-missing})" 20

PARTTYPE="$(lsblk -no PARTTYPE "$PART" 2>/dev/null | head -1 || true)"
FSTYPE="$(lsblk -no FSTYPE "$PART" 2>/dev/null | head -1 || true)"
[[ -n "$PARTTYPE" ]] || fail "no ESP partition found" 21
echo "PARTTYPE=${PARTTYPE} FSTYPE=${FSTYPE}"

PARTTYPE_LC="$(echo "$PARTTYPE" | tr '[:upper:]' '[:lower:]')"
if [[ "$PARTTYPE_LC" != *"efi"* && "$PARTTYPE_LC" != *"ef00"* && "$PARTTYPE_LC" != *"${EFI_PARTTYPE_UUID}"* ]]; then
  fail "partition not EFI System (PARTTYPE=${PARTTYPE})" 21
fi

[[ "$FSTYPE" == "vfat" || "$FSTYPE" == "msdos" ]] || fail "partition not FAT32/vfat (FSTYPE=${FSTYPE})" 22

PARTLABEL="$(lsblk -no PARTLABEL "$PART" 2>/dev/null | head -1 || true)"
FAT_LABEL="$(read_fat_volume_label "$PART")"
echo "PARTLABEL=${PARTLABEL:-} FAT_LABEL=${FAT_LABEL:-}"

[[ "$PARTLABEL" == "$EXPECTED_GPT_PART_NAME" ]] || fail "GPT partition name expected ${EXPECTED_GPT_PART_NAME} got ${PARTLABEL:-missing}" 22

if [[ -z "$FAT_LABEL" || "$FAT_LABEL" != "$EXPECTED_FAT_LABEL" ]]; then
  fail "FAT volume label expected ${EXPECTED_FAT_LABEL} got ${FAT_LABEL:-missing} — repair: sudo fatlabel ${PART} ${EXPECTED_FAT_LABEL}" 22
fi

MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
WAS_MOUNTED=false
if [[ -z "$MOUNT" ]]; then
  if command -v udisksctl >/dev/null; then
    udisksctl mount -b "$PART" --options ro >/dev/null 2>&1 || fail "read-only mount failed" 28
    MOUNT="$(lsblk -no MOUNTPOINTS "$PART" 2>/dev/null | head -1 || true)"
  else
    fail "read-only mount failed (no udisksctl)" 28
  fi
else
  WAS_MOUNTED=true
fi

[[ -n "$MOUNT" && -d "$MOUNT" ]] || fail "read-only mount failed" 28

cleanup() {
  if [[ "$WAS_MOUNTED" != true && -n "$MOUNT" ]]; then
    udisksctl unmount -b "$PART" >/dev/null 2>&1 || true
    sync || true
  fi
}
trap cleanup EXIT

check_file() {
  local rel="$1" code="$2"
  if [[ ! -e "$MOUNT/$rel" ]]; then
    fail "missing $rel" "$code"
  fi
  echo "OK: $rel"
}

check_file "EFI/BOOT/BOOTX64.EFI" 23
check_file "boot/grub/grub.cfg" 24
check_file "live/vmlinuz" 25
check_file "live/initrd.img" 25
check_file "live/filesystem.squashfs" 26

if [[ -e "$MOUNT/.sqtmp" ]]; then
  fail "staging artifact .sqtmp must not be on USB" 26
fi

if grep -q "menuentry \"Setuphelfer Rettung starten\"" "$MOUNT/boot/grub/grub.cfg" 2>/dev/null; then
  echo "OK: grub menu Setuphelfer Rettung starten"
else
  fail "grub.cfg missing required menu entry" 24
fi

SQ_SIZE="$(stat -c '%s' "$MOUNT/live/filesystem.squashfs" 2>/dev/null || echo 0)"
echo "filesystem.squashfs size_bytes=${SQ_SIZE}"
[[ "$SQ_SIZE" -gt 100000000 ]] || fail "filesystem.squashfs size implausible" 26

echo "OK: FAT32 ESP rescue USB verified read-only on ${PART} mount=${MOUNT} fat_label=${EXPECTED_FAT_LABEL} gpt_name=${EXPECTED_GPT_PART_NAME}"
exit 0
