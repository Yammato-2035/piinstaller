#!/usr/bin/env bash
# Read-only: prüft UEFI-x64-Bootfähigkeit einer Rescue-Hybrid-ISO.
# Exit 0  = UEFI-x64-ready (BIOS + EFI El Torito + BOOTX64.EFI)
# Exit 30 = Usage
# Exit 31 = ISO fehlt
# Exit 32 = RESCUE-UEFI-001 efi_boot_files_missing
# Exit 33 = RESCUE-UEFI-002 efi_eltorito_entry_missing
# Exit 34 = RESCUE-UEFI-003 isolinux_only_iso
# Exit 35 = RESCUE-UEFI-004 msi_uefi_boot_failed_confirmed (optional --require-target-boot)
# Exit 36 = RESCUE-UEFI-005 windows_inspect_blocked_by_rescue_uefi_boot (optional --emit-inspect-blocker)
set -euo pipefail

ISO=""
REQUIRE_TARGET_BOOT=false
EMIT_INSPECT_BLOCKER=false

usage() {
  cat <<EOF
Usage: $0 [--require-target-boot] [--emit-inspect-blocker] /path/to/binary.hybrid.iso

Checks:
  - ISO exists, SHA256 printable
  - xorriso El Torito report contains BIOS boot (isolinux)
  - xorriso El Torito report contains EFI alt-boot or EFI image
  - /EFI/BOOT/BOOTX64.EFI present on ISO (or in EFI El Torito image)
  - does not classify isolinux-only ISO as UEFI-ready
EOF
  exit 30
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-target-boot) REQUIRE_TARGET_BOOT=true; shift ;;
    --emit-inspect-blocker) EMIT_INSPECT_BLOCKER=true; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
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
trap 'rm -f "$REPORT"' EXIT
xorriso -indev "$ISO" -report_el_torito as_mkisofs 2>/dev/null >"$REPORT" || true

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

_has_bootx64=false
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

if [[ "$_has_bios" == true && "$_has_efi_eltorito" != true && "$_has_bootx64" != true ]]; then
  echo "RESCUE-UEFI-003: isolinux_only_iso (BIOS hybrid without UEFI path)" >&2
  echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  echo "RESCUE-UEFI-001: efi_boot_files_missing (/EFI/BOOT/BOOTX64.EFI absent)" >&2
  exit 34
fi

if [[ "$_has_bootx64" != true ]]; then
  echo "RESCUE-UEFI-001: efi_boot_files_missing (/EFI/BOOT/BOOTX64.EFI absent)" >&2
  exit 32
fi

if [[ "$_has_efi_eltorito" != true ]]; then
  echo "RESCUE-UEFI-002: efi_eltorito_entry_missing" >&2
  exit 33
fi

if [[ "$REQUIRE_TARGET_BOOT" == true ]]; then
  echo "RESCUE-UEFI-004: msi_uefi_boot_failed_confirmed (target UEFI boot not validated)" >&2
  exit 35
fi

if [[ "$EMIT_INSPECT_BLOCKER" == true ]]; then
  echo "RESCUE-UEFI-005: windows_inspect_blocked_by_rescue_uefi_boot" >&2
  exit 36
fi

echo "OK: rescue ISO UEFI-x64 — BIOS=${_has_bios} EFI_ELTORITO=${_has_efi_eltorito} BOOTX64=${_has_bootx64} SHA256=${SHA256}"
exit 0
