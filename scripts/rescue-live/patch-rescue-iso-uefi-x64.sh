#!/usr/bin/env bash
# Repacks an existing isolinux iso-hybrid Rescue ISO with UEFI-x64 El Torito boot.
# Requires: xorriso, grub-mkstandalone, mkfs.vfat, mcopy, isohybrid.
# Does NOT run lb build, dd, apt, or USB writes.
# Exit 0 ok | 20 usage | 21 missing ISO | 22 toolchain | 23 extract | 24 patch
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_IN=""
ISO_OUT=""
IN_PLACE=false

usage() {
  cat <<EOF
Usage: $0 [--in-place] /path/to/binary.hybrid.iso [output.iso]

Adds UEFI-x64 boot to an existing Setuphelfer Rescue iso-hybrid:
  - /EFI/BOOT/BOOTX64.EFI (grub-mkstandalone)
  - boot/grub/efi.img + EFI El Torito entry (xorriso)
  - preserves isolinux BIOS hybrid boot

Without --in-place, writes <input>.uefi.iso unless output path is given.
After patch, run: scripts/rescue-live/validate-rescue-iso-uefi-boot.sh <iso>
EOF
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --in-place) IN_PLACE=true; shift ;;
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

if [[ -z "$ISO_OUT" ]]; then
  if [[ "$IN_PLACE" == true ]]; then
    ISO_OUT="${ISO_IN}.tmp.uefi.$$"
  else
    ISO_OUT="${ISO_IN%.iso}.uefi.iso"
    [[ "$ISO_OUT" == "$ISO_IN" ]] && ISO_OUT="${ISO_IN}.uefi.iso"
  fi
fi

WORK="$(mktemp -d)"
STAGING="${WORK}/staging"
GRUB_CFG="${WORK}/grub.cfg"
BOOTX64="${WORK}/BOOTX64.EFI"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

mkdir -p "$STAGING"
xorriso -osirrox on -indev "$ISO_IN" -extract / "$STAGING" 2>/dev/null \
  || { echo "ERROR: xorriso extract failed" >&2; exit 23; }

LIVE_CFG=""
for candidate in isolinux/live.cfg ISOLINUX/LIVE.CFG; do
  if [[ -f "$STAGING/$candidate" ]]; then
    LIVE_CFG="$STAGING/$candidate"
    break
  fi
done
[[ -n "$LIVE_CFG" ]] || { echo "ERROR: isolinux live.cfg missing in ISO" >&2; exit 23; }

BOOTAPPEND="$(awk '
  /^[[:space:]]*append[[:space:]]/ {
    sub(/^[[:space:]]*append[[:space:]]+/, "", $0)
    print $0
    exit
  }
' "$LIVE_CFG")"
[[ -n "$BOOTAPPEND" ]] || { echo "ERROR: could not parse bootappend from live.cfg" >&2; exit 23; }

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
  || { echo "ERROR: grub-mkstandalone failed" >&2; exit 24; }

mkdir -p "$STAGING/EFI/BOOT" "$STAGING/boot/grub"
install -m 0644 "$BOOTX64" "$STAGING/EFI/BOOT/BOOTX64.EFI"
install -m 0644 "$GRUB_CFG" "$STAGING/boot/grub/grub.cfg"

EFI_IMG="$STAGING/boot/grub/efi.img"
dd if=/dev/zero of="$EFI_IMG" bs=1M count=4 status=none
mkfs.vfat -F 16 -n EFIBOOT "$EFI_IMG" >/dev/null
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
  || { echo "ERROR: xorriso mkisofs failed" >&2; exit 24; }

isohybrid "$ISO_OUT" 2>/dev/null || true

if [[ "$IN_PLACE" == true ]]; then
  mv -f "$ISO_OUT" "$ISO_IN"
  ISO_OUT="$ISO_IN"
fi

SHA256="$(sha256sum "$ISO_OUT" | awk '{print $1}')"
echo "OK: UEFI-x64 patch applied"
echo "ISO_OUT=${ISO_OUT}"
echo "ISO_SHA256=${SHA256}"
echo "NEXT: ${SCRIPT_DIR}/validate-rescue-iso-uefi-boot.sh ${ISO_OUT}"
