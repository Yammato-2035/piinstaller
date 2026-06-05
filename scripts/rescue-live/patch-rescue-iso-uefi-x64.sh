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

# mkfs.vfat -C count on Debian bookworm: file size = count × 1024 bytes (16 MiB => 16384).
# El Torito -e limit: boot image ≤ 65535 × 512 bytes (~32 MiB − 512 B).
ESP_SIZE_MIB=16
ESP_SECTOR_COUNT=16384
ESP_SIZE_BYTES=16777216
ESP_MAX_BYTES=$((65535 * 512))
ISO_EFI_IMG_PATH="boot/grub/efi.img"
ISO_BOOTX64_PATH="EFI/BOOT/BOOTX64.EFI"

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

debug_esp_paths() {
  local host_esp="$1"
  local staging_esp="$2"
  echo "UEFI_PATCH_DEBUG: ESP_HOST=$host_esp"
  echo "UEFI_PATCH_DEBUG: ESP_HOST_ABS=$(readlink -f "$host_esp" 2>/dev/null || echo missing)"
  echo "UEFI_PATCH_DEBUG: ESP_STAGING=$staging_esp"
  ls -lh "$host_esp" "$staging_esp" 2>/dev/null || true
  stat "$host_esp" 2>/dev/null || true
  du -h "$host_esp" 2>/dev/null || true
  echo "UEFI_PATCH_DEBUG: XORRISO_E_ISO_PATH=${ISO_EFI_IMG_PATH}"
  echo "UEFI_PATCH_DEBUG: XORRISO_APPEND_HOST=$(readlink -f "$host_esp" 2>/dev/null || echo missing)"
}

resolve_isohybrid_mbr() {
  for candidate in \
    /usr/lib/ISOLINUX/isohdpfx.bin \
    /usr/lib/syslinux/isohdpfx.bin \
    /usr/share/syslinux/isohdpfx.bin; do
    if [[ -f "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
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
    "schema_version": 2,
    "mode": "plan_only",
    "iso_in": ${ISO_IN@Q},
    "iso_out": ${ISO_OUT@Q},
    "in_place": bool(int("${IN_PLACE_FLAG}")),
    "iso_sha256_in": ${ISO_SHA256_IN@Q},
    "iso_size_bytes_in": int(${ISO_SIZE_IN:-0}),
    "esp_size_mib": ${ESP_SIZE_MIB},
    "esp_sector_count": ${ESP_SECTOR_COUNT},
    "esp_size_bytes": ${ESP_SIZE_BYTES},
    "esp_create_method": "mkfs.vfat -C count=16384 (16 MiB on Debian bookworm)",
    "esp_host_path": "\$WORKDIR/efi.img",
    "iso_internal_bootx64": "/EFI/BOOT/BOOTX64.EFI",
    "iso_internal_efi_img": "${ISO_EFI_IMG_PATH}",
    "xorriso_e_arg": "${ISO_EFI_IMG_PATH}",
    "xorriso_append_partition_arg": "absolute host path to \$WORKDIR/efi.img",
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
ESP_HOST="${WORK}/efi.img"
STAGING_EFI="${STAGING}/${ISO_EFI_IMG_PATH}"
cleanup() { rm -rf "$WORK" 2>/dev/null || true; }
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

rm -f "$ESP_HOST"
if ! mkfs.vfat -C "$ESP_HOST" "$ESP_SECTOR_COUNT" -n EFIBOOT >/dev/null 2>&1; then
  fail_mkfs
fi
[[ -s "$ESP_HOST" ]] || fail_mkfs
ESP_IMG_ABS="$(readlink -f "$ESP_HOST")"
[[ -r "$ESP_IMG_ABS" ]] || fail_xorriso "ESP host image not readable: ${ESP_IMG_ABS}"

ACTUAL_ESP_SIZE="$(stat -c '%s' "$ESP_HOST" 2>/dev/null || echo 0)"
if [[ "$ACTUAL_ESP_SIZE" -lt 4194304 ]]; then
  fail_esp_size
fi
if [[ "$ACTUAL_ESP_SIZE" -gt "$ESP_MAX_BYTES" ]]; then
  fail_xorriso "ESP image ${ACTUAL_ESP_SIZE} bytes exceeds El Torito limit ${ESP_MAX_BYTES}"
fi

MTOOLS_SKIP_CHECK=1 mmd -i "$ESP_HOST" ::EFI ::EFI/BOOT
MTOOLS_SKIP_CHECK=1 mcopy -i "$ESP_HOST" "$BOOTX64" ::EFI/BOOT/BOOTX64.EFI

install -m 0644 "$ESP_HOST" "$STAGING_EFI"
[[ -s "$STAGING_EFI" ]] || fail_xorriso "staging efi.img missing after copy"

debug_esp_paths "$ESP_HOST" "$STAGING_EFI"

VOL="$(xorriso -indev "$ISO_IN" -report_el_torito as_mkisofs 2>/dev/null | sed -n "s/^-V '\(.*\)'/\1/p" | head -1)"
[[ -n "$VOL" ]] || VOL="SETUPHELFER_RESCUE"

ISOHYBRID_MBR=""
if ISOHYBRID_MBR="$(resolve_isohybrid_mbr)"; then
  :
else
  echo "UEFI_PATCH_DEBUG: isohybrid-mbr template not found — continuing without -isohybrid-mbr" >&2
fi

XORRISO_LOG="${WORK}/xorriso-mkisofs.log"
XORRISO_ARGS=(
  -as mkisofs
  -iso-level 3
  -full-iso9660-filenames
  -volid "$VOL"
  -J -joliet-long -r
  -output "$ISO_OUT"
  -eltorito-boot isolinux/isolinux.bin
  -eltorito-catalog isolinux/boot.cat
  -no-emul-boot
  -boot-load-size 4
  -boot-info-table
  -eltorito-alt-boot
  -e "$ISO_EFI_IMG_PATH"
  -no-emul-boot
  -isohybrid-gpt-basdat
  -append_partition 2 0xef "$ESP_IMG_ABS"
)

if [[ -n "$ISOHYBRID_MBR" ]]; then
  XORRISO_ARGS+=( -isohybrid-mbr "$ISOHYBRID_MBR" -partition_offset 16 )
fi

echo "UEFI_PATCH_DEBUG: xorriso ${XORRISO_ARGS[*]} $STAGING"
if ! xorriso "${XORRISO_ARGS[@]}" "$STAGING" >"$XORRISO_LOG" 2>&1; then
  tail -40 "$XORRISO_LOG" >&2 || true
  fail_xorriso "xorriso mkisofs failed esp_bytes=${ACTUAL_ESP_SIZE} append=${ESP_IMG_ABS} e=${ISO_EFI_IMG_PATH}"
fi

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
echo "ESP_APPEND_HOST=${ESP_IMG_ABS}"
echo "EFI_ELTORITO_ISO_PATH=${ISO_EFI_IMG_PATH}"
echo "NEXT: ${SCRIPT_DIR}/validate-rescue-iso-uefi-boot.sh ${ISO_OUT}"
