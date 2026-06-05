#!/usr/bin/env bash
# Repacks an existing isolinux iso-hybrid Rescue ISO with UEFI-x64 El Torito boot.
# Requires: xorriso, grub-mkstandalone, mkfs.vfat, mcopy, isohybrid.
# Does NOT run lb build, dd, apt, USB writes, or block-device access.
#
# Exit  0 ok
# Exit 20 usage
# Exit 21 missing ISO
# Exit 22 toolchain
# Exit 23 extract / live.cfg
# Exit 24 patch (generic)
# Exit 41 RESCUE-UEFI-PATCH-ESP-SIZE-001
# Exit 42 RESCUE-UEFI-PATCH-MKFS-001
# Exit 43 RESCUE-UEFI-PATCH-GRUB-001
# Exit 44 RESCUE-UEFI-PATCH-XORRISO-001
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_IN=""
ISO_OUT=""
IN_PLACE=false
PLAN_ONLY=false
DRY_RUN=false

# FAT ESP image: mkfs.vfat -F 16 fails on 4 MiB (too small). Use 16 MiB via -C (32768 × 512 B).
ESP_SECTOR_COUNT=32768
ESP_SIZE_BYTES=$((ESP_SECTOR_COUNT * 512))

usage() {
  cat <<EOF
Usage: $0 [--in-place] [--plan-only|--dry-run] /path/to/binary.hybrid.iso [output.iso]

Adds UEFI-x64 boot to an existing Setuphelfer Rescue iso-hybrid:
  - /EFI/BOOT/BOOTX64.EFI (grub-mkstandalone)
  - boot/grub/efi.img + EFI El Torito entry (xorriso)
  - preserves isolinux BIOS hybrid boot

--plan-only / --dry-run: print JSON plan only (no ISO mutation, no root-owned overwrite).

After patch, run: scripts/rescue-live/validate-rescue-iso-uefi-boot.sh <iso>
EOF
  exit 20
}

fail_esp_size() {
  echo "RESCUE-UEFI-PATCH-ESP-SIZE-001: invalid ESP size sectors=${ESP_SECTOR_COUNT} bytes=${ESP_SIZE_BYTES}" >&2
  exit 41
}

fail_mkfs() {
  echo "RESCUE-UEFI-PATCH-MKFS-001: mkfs.vfat failed for ESP image" >&2
  exit 42
}

fail_grub() {
  echo "RESCUE-UEFI-PATCH-GRUB-001: grub-mkstandalone failed" >&2
  exit 43
}

fail_xorriso() {
  echo "RESCUE-UEFI-PATCH-XORRISO-001: $*" >&2
  exit 44
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in-place) IN_PLACE=true; shift ;;
    --plan-only|--dry-run) PLAN_ONLY=true; DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
    *)
      if [[ -z "$ISO_IN" ]]; then
        ISO_IN="$1"
      elif [[ -z "$ISO_OUT" ]]; then
        ISO_OUT="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage
      fi
      shift
      ;;
  esac
done

[[ -n "$ISO_IN" && -f "$ISO_IN" ]] || { echo "ERROR: ISO missing: ${ISO_IN:-}" >&2; exit 21; }

for tool in xorriso grub-mkstandalone mkfs.vfat mcopy isohybrid rsync; do
  command -v "$tool" >/dev/null || { echo "ERROR: missing toolchain: $tool" >&2; exit 22; }
done

if [[ "$ESP_SECTOR_COUNT" -lt 8192 || "$ESP_SIZE_BYTES" -lt 4194304 ]]; then
  fail_esp_size
fi

if [[ -z "$ISO_OUT" ]]; then
  if [[ "$IN_PLACE" == true ]]; then
    ISO_OUT="${ISO_IN}.tmp.uefi.$$"
  else
    ISO_OUT="${ISO_IN%.iso}.uefi.iso"
    [[ "$ISO_OUT" == "$ISO_IN" ]] && ISO_OUT="${ISO_IN}.uefi.iso"
  fi
fi

ISO_SHA256_IN="$(sha256sum "$ISO_IN" | awk '{print $1}')"
ISO_SIZE_IN="$(stat -c '%s' "$ISO_IN" 2>/dev/null || echo "")"
IN_PLACE_FLAG=0
[[ "$IN_PLACE" == true ]] && IN_PLACE_FLAG=1

if [[ "$PLAN_ONLY" == true ]]; then
  python3 - <<PY
import json
print(json.dumps({
    "schema_version": 1,
    "mode": "plan_only",
    "iso_in": ${ISO_IN@Q},
    "iso_out": ${ISO_OUT@Q},
    "in_place": bool(int("${IN_PLACE_FLAG}")),
    "iso_sha256_in": ${ISO_SHA256_IN@Q},
    "iso_size_bytes_in": int(${ISO_SIZE_IN:-0}),
    "esp_sector_count": ${ESP_SECTOR_COUNT},
    "esp_size_bytes": ${ESP_SIZE_BYTES},
    "esp_create_method": "mkfs.vfat -C",
    "bootx64_path": "/EFI/BOOT/BOOTX64.EFI",
    "efi_img_path": "boot/grub/efi.img",
    "eltorito_efi_entry": "-eltorito-alt-boot -e boot/grub/efi.img",
    "devices_touched": False,
    "usb_write": False,
}, indent=2))
PY
  exit 0
fi

WORK="$(mktemp -d)"
STAGING="${WORK}/staging"
GRUB_CFG="${WORK}/grub.cfg"
BOOTX64="${WORK}/BOOTX64.EFI"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

mkdir -p "$STAGING"
xorriso -osirrox on -indev "$ISO_IN" -extract / "$STAGING" 2>/dev/null \
  || fail_xorriso "xorriso extract failed"

LIVE_CFG=""
for candidate in isolinux/live.cfg ISOLINUX/LIVE.CFG; do
  if [[ -f "$STAGING/$candidate" ]]; then
    LIVE_CFG="$STAGING/$candidate"
    break
  fi
done
[[ -n "$LIVE_CFG" ]] || fail_xorriso "isolinux live.cfg missing in ISO"

BOOTAPPEND="$(awk '
  /^[[:space:]]*append[[:space:]]/ {
    sub(/^[[:space:]]*append[[:space:]]+/, "", $0)
    print $0
    exit
  }
' "$LIVE_CFG")"
[[ -n "$BOOTAPPEND" ]] || fail_xorriso "could not parse bootappend from live.cfg"

cat >"$GRUB_CFG" <<EOF
set timeout=5
set default=0
search --set=root --file /live/filesystem.squashfs
menuentry "Setuphelfer Rescue Live" {
  linux /live/vmlinuz ${BOOTAPPEND}
  initrd /live/initrd.img
}
EOF

grub-mkstandalone \
  --format=x86_64-efi \
  --output="$BOOTX64" \
  --locales="" \
  --fonts="" \
  "boot/grub/grub.cfg=$GRUB_CFG" \
  || fail_grub

[[ -s "$BOOTX64" ]] || fail_grub

mkdir -p "$STAGING/EFI/BOOT" "$STAGING/boot/grub"
install -m 0644 "$BOOTX64" "$STAGING/EFI/BOOT/BOOTX64.EFI"
install -m 0644 "$GRUB_CFG" "$STAGING/boot/grub/grub.cfg"

EFI_IMG="$STAGING/boot/grub/efi.img"
rm -f "$EFI_IMG"
if ! mkfs.vfat -C "$EFI_IMG" "$ESP_SECTOR_COUNT" -n EFIBOOT >/dev/null 2>&1; then
  fail_mkfs
fi
ACTUAL_ESP_SIZE="$(stat -c '%s' "$EFI_IMG" 2>/dev/null || echo 0)"
if [[ "$ACTUAL_ESP_SIZE" -lt "$ESP_SIZE_BYTES" ]]; then
  fail_esp_size
fi
MTOOLS_SKIP_CHECK=1 mmd -i "$EFI_IMG" ::EFI ::EFI/BOOT
MTOOLS_SKIP_CHECK=1 mcopy -i "$EFI_IMG" "$BOOTX64" ::EFI/BOOT/BOOTX64.EFI

VOL="$(xorriso -indev "$ISO_IN" -report_el_torito as_mkisofs 2>/dev/null | sed -n "s/^-V '\(.*\)'/\1/p" | head -1)"
[[ -n "$VOL" ]] || VOL="SETUPHELFER_RESCUE"

xorriso -as mkisofs \
  -iso-level 3 \
  -full-iso9660-filenames \
  -volid "$VOL" \
  -J -joliet-long \
  -output "$ISO_OUT" \
  -eltorito-boot isolinux/isolinux.bin \
  -eltorito-catalog isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot \
  -e boot/grub/efi.img \
  -no-emul-boot \
  -append_partition 2 0xef boot/grub/efi.img \
  -appended_part_as_gpt \
  -isohybrid-gpt-basdat \
  "$STAGING" \
  || fail_xorriso "xorriso mkisofs failed"

isohybrid "$ISO_OUT" 2>/dev/null || true

if [[ "$IN_PLACE" == true ]]; then
  mv -f "$ISO_OUT" "$ISO_IN"
  ISO_OUT="$ISO_IN"
fi

SHA256="$(sha256sum "$ISO_OUT" | awk '{print $1}')"
echo "OK: UEFI-x64 patch applied"
echo "ISO_OUT=${ISO_OUT}"
echo "ISO_SHA256=${SHA256}"
echo "ISO_SHA256_BEFORE=${ISO_SHA256_IN}"
echo "ESP_SIZE_BYTES=${ESP_SIZE_BYTES}"
echo "NEXT: ${SCRIPT_DIR}/validate-rescue-iso-uefi-boot.sh ${ISO_OUT}"
