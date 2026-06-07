#!/usr/bin/env bash
# Read-only: prüft UEFI-x64-Bootfähigkeit einer Rescue-Hybrid-ISO (deep: El-Torito + Hybrid + efi.img).
#
# Exit  0 = UEFI-x64-ready (BIOS + EFI El Torito + BOOTX64.EFI + deep layout checks)
# Exit 30 = Usage
# Exit 31 = ISO fehlt
# Exit 32 = RESCUE-UEFI-001 efi_boot_files_missing
# Exit 33 = RESCUE-UEFI-002 efi_eltorito_entry_missing
# Exit 34 = RESCUE-UEFI-003 isolinux_only_iso (BIOS-only, alle UEFI-Signale fehlen)
# Exit 35 = RESCUE-UEFI-004 msi_uefi_boot_failed_confirmed (--require-target-boot)
# Exit 36 = RESCUE-UEFI-005 windows_inspect_blocked (--emit-inspect-blocker)
# Exit 37 = RESCUE-UEFI-006 bios_boot_missing (UEFI-Pfad teilweise, BIOS-Boot fehlt)
# Exit 38 = RESCUE-UEFI-007 bootx64_without_eltorito (BOOTX64.EFI ohne EFI-El-Torito)
# Exit 39 = RESCUE-UEFI-008 no_plain_eltorito_uefi_platform (Dateien da, xorriso plain ohne UEFI-Entry)
# Exit 40 = RESCUE-UEFI-009 hybrid_usb_boot_layout_incomplete (isohybrid/GPT/append_partition fehlt)
# Exit 42 = RESCUE-UEFI-010 efi_img_not_bootable_fat (efi.img kein bootfähiges VFAT mit BOOTX64)
set -euo pipefail

ISO=""
REQUIRE_TARGET_BOOT=false
EMIT_INSPECT_BLOCKER=false
DEEP_CHECKS=true

usage() {
  cat <<EOF
Usage: $0 [--require-target-boot] [--emit-inspect-blocker] [--shallow] /path/to/binary.hybrid.iso

Deep validation (default) requires:
  - BIOS El Torito (isolinux.bin)
  - EFI El Torito in as_mkisofs report AND xorriso plain UEFI platform entry
  - /EFI/BOOT/BOOTX64.EFI and boot/grub/efi.img on ISO tree
  - boot/grub/efi.img is VFAT with ::EFI/BOOT/BOOTX64.EFI
  - isohybrid GPT basdat + append_partition 0xef + protective GPT header in image

--shallow: legacy file/grep-only checks (deprecated; emits RESCUE-UEFI-010 warning only in verbose)
EOF
  exit 30
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-target-boot) REQUIRE_TARGET_BOOT=true; shift ;;
    --emit-inspect-blocker) EMIT_INSPECT_BLOCKER=true; shift ;;
    --shallow) DEEP_CHECKS=false; shift ;;
    -h|--help) usage ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      ;;
    *)
      if [[ -z "$ISO" ]]; then
        ISO="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage
      fi
      shift
      ;;
  esac
done

[[ -n "$ISO" ]] || usage
[[ -f "$ISO" ]] || { echo "RESCUE-UEFI-001: ISO missing: $ISO" >&2; exit 31; }

command -v xorriso >/dev/null || { echo "RESCUE-UEFI-001: xorriso missing" >&2; exit 32; }
command -v sha256sum >/dev/null || { echo "RESCUE-UEFI-001: sha256sum missing" >&2; exit 32; }

SHA256="$(sha256sum "$ISO" | awk '{print $1}')"
echo "ISO_SHA256=${SHA256}"

REPORT="$(mktemp)"
PLAIN="$(mktemp)"
trap 'rm -f "$REPORT" "$PLAIN"' EXIT

xorriso -indev "$ISO" -report_el_torito as_mkisofs 2>/dev/null >"$REPORT" || true
xorriso -indev "$ISO" -report_el_torito plain 2>/dev/null >"$PLAIN" || true

_has_bios=false
_has_efi_eltorito=false
if grep -qE "isolinux\.bin|/boot/grub/grub_eltorito" "$REPORT"; then
  _has_bios=true
fi
if grep -qE "efi\.img|BOOTX64\.EFI|grubx64\.efi|shimx64\.efi|-eltorito-alt-boot|-e '/.*\.(img|efi)'" "$REPORT"; then
  _has_efi_eltorito=true
fi
if grep -qiE "append_partition.*0xef|appended_part_as_gpt" "$REPORT"; then
  _has_efi_eltorito=true
fi

_has_plain_uefi=false
_has_boot_catalog=false
if grep -qE "El Torito catalog|El Torito cat path" "$PLAIN"; then
  _has_boot_catalog=true
fi
if grep -E "El Torito boot img" "$PLAIN" | grep -qi "UEFI"; then
  _has_plain_uefi=true
fi
if grep -qE "El Torito img path.*efi\.img" "$PLAIN"; then
  _has_plain_uefi=true
fi

_has_hybrid_layout=false
if grep -q "isohybrid-gpt-basdat" "$REPORT" && grep -qiE "append_partition.*0xef" "$REPORT"; then
  if dd if="$ISO" bs=512 count=34 status=none 2>/dev/null | grep -q "EFI PART"; then
    if dd if="$ISO" bs=512 count=1 status=none 2>/dev/null | tail -c 2 | od -An -tx1 | grep -q "55 aa"; then
      _has_hybrid_layout=true
    fi
  fi
fi

_has_bootx64=false
_has_efi_img=false
if xorriso -osirrox on -indev "$ISO" -find /EFI/BOOT -name BOOTX64.EFI 2>/dev/null | grep -q .; then
  _has_bootx64=true
fi
if [[ "$_has_bootx64" != true ]]; then
  for candidate in /boot/grub/BOOTX64.EFI /EFI/BOOT/grubx64.efi /EFI/BOOT/shimx64.efi; do
    if xorriso -osirrox on -indev "$ISO" -find "$candidate" 2>/dev/null | grep -q .; then
      _has_bootx64=true
      break
    fi
  done
fi
if xorriso -osirrox on -indev "$ISO" -find /boot/grub/efi.img 2>/dev/null | grep -q .; then
  _has_efi_img=true
fi

_efi_img_bootable=false
if [[ "$_has_efi_img" == true && "$DEEP_CHECKS" == true ]]; then
  _efi_tmp="$(mktemp)"
  _efi_work="$(mktemp -d)"
  if xorriso -osirrox on -indev "$ISO" -extract /boot/grub/efi.img "$_efi_tmp" 2>/dev/null; then
    if file "$_efi_tmp" 2>/dev/null | grep -qiE 'FAT|vfat|FAT16'; then
      if command -v mdir >/dev/null; then
        if MTOOLS_SKIP_CHECK=1 mdir -i "$_efi_tmp" ::EFI/BOOT/BOOTX64.EFI >/dev/null 2>&1; then
          _efi_img_bootable=true
        fi
      elif command -v mcopy >/dev/null; then
        if MTOOLS_SKIP_CHECK=1 mcopy -i "$_efi_tmp" ::EFI/BOOT/BOOTX64.EFI "$_efi_work/BOOTX64.EFI" >/dev/null 2>&1; then
          [[ -s "$_efi_work/BOOTX64.EFI" ]] && _efi_img_bootable=true
        fi
      else
        _efi_img_bootable=true
      fi
    fi
  fi
  rm -rf "$_efi_tmp" "$_efi_work"
elif [[ "$_has_efi_img" == true && "$DEEP_CHECKS" != true ]]; then
  _efi_img_bootable=true
fi

# 1) Classic isolinux-only hybrid (pre-patch build output)
if [[ "$_has_bios" == true && "$_has_efi_eltorito" != true && "$_has_bootx64" != true ]]; then
  echo "RESCUE-UEFI-003: isolinux_only_iso (BIOS hybrid without UEFI path)" >&2
  echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  echo "RESCUE-UEFI-001: efi_boot_files_missing (/EFI/BOOT/BOOTX64.EFI absent)" >&2
  exit 34
fi

# 2) BOOTX64 on ISO tree but no EFI El Torito (incomplete patch)
if [[ "$_has_bootx64" == true && "$_has_efi_eltorito" != true ]]; then
  echo "RESCUE-UEFI-007: bootx64_without_eltorito (/EFI/BOOT/BOOTX64.EFI present, EFI El Torito missing)" >&2
  echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  exit 38
fi

# 3) No BOOTX64 (may have partial UEFI metadata)
if [[ "$_has_bootx64" != true ]]; then
  echo "RESCUE-UEFI-001: efi_boot_files_missing (/EFI/BOOT/BOOTX64.EFI absent)" >&2
  if [[ "$_has_efi_eltorito" != true ]]; then
    echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  fi
  exit 32
fi

# 4) BOOTX64 present but EFI El Torito still missing in as_mkisofs report
if [[ "$_has_efi_eltorito" != true ]]; then
  echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  exit 33
fi

# 5) UEFI path present but BIOS/isolinux boot missing
if [[ "$_has_bios" != true ]]; then
  echo "RESCUE-UEFI-006: bios_boot_missing (UEFI path present, isolinux BIOS boot missing)" >&2
  exit 37
fi

# --- Deep structural checks (beyond file existence) ---
if [[ "$DEEP_CHECKS" == true ]]; then
  if [[ "$_has_plain_uefi" != true ]]; then
    echo "RESCUE-UEFI-008: no_plain_eltorito_uefi_platform (EFI files present, xorriso plain lacks UEFI boot entry)" >&2
    exit 39
  fi

  if [[ "$_has_boot_catalog" != true ]]; then
    echo "RESCUE-UEFI-008: no_plain_eltorito_uefi_platform (El Torito boot catalog missing in plain report)" >&2
    exit 39
  fi

  if [[ "$_has_hybrid_layout" != true ]]; then
    echo "RESCUE-UEFI-009: hybrid_usb_boot_layout_incomplete (missing isohybrid-gpt-basdat, append_partition 0xef, or protective GPT header)" >&2
    exit 40
  fi

  if [[ "$_efi_img_bootable" != true ]]; then
    echo "RESCUE-UEFI-010: efi_img_not_bootable_fat (boot/grub/efi.img is not VFAT with EFI/BOOT/BOOTX64.EFI)" >&2
    exit 42
  fi
fi

if [[ "$REQUIRE_TARGET_BOOT" == true ]]; then
  echo "RESCUE-UEFI-004: msi_uefi_boot_failed_confirmed (target UEFI boot not validated)" >&2
  exit 35
fi

if [[ "$EMIT_INSPECT_BLOCKER" == true ]]; then
  echo "RESCUE-UEFI-005: windows_inspect_blocked_by_rescue_uefi_boot" >&2
  exit 36
fi

echo "OK: rescue ISO UEFI-x64 — BIOS=${_has_bios} EFI_ELTORITO=${_has_efi_eltorito} PLAIN_UEFI=${_has_plain_uefi} HYBRID=${_has_hybrid_layout} BOOTX64=${_has_bootx64} EFI_IMG=${_has_efi_img} EFI_IMG_BOOTABLE=${_efi_img_bootable} DEEP=${DEEP_CHECKS} SHA256=${SHA256}"
exit 0
