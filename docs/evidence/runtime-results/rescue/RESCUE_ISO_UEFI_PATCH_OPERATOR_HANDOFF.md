# RESCUE ISO UEFI Patch — Operator Handoff

**Status:** `awaiting_operator_in_place_patch`  
**Root cause fixed in workspace:** xorriso `-append_partition` absolute host path + ESP 16 MiB (`mkfs.vfat -C 16384`)

## Voraussetzungen

- Controlled Build `LB_EXIT=0`, ISO vorhanden (root-owned)
- Operator-Terminal mit `sudo`
- **Kein USB-Write** in diesem Schritt

## Operator-Befehle

```bash
cd /home/volker/piinstaller

ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso

ls -lh "$ISO"
sha256sum "$ISO"
file "$ISO"

./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO" || true
./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --plan-only "$ISO"

sudo ./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place "$ISO"

./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"
sha256sum "$ISO"
file "$ISO"
xorriso -indev "$ISO" -report_el_torito as_mkisofs
xorriso -indev "$ISO" -find /EFI/BOOT/BOOTX64.EFI -type f -print 2>/dev/null || true
xorriso -indev "$ISO" -find /boot/grub/efi.img -type f -print 2>/dev/null || true
```

## Erfolgskriterien

| Check | Erwartung |
|-------|-----------|
| Patch Exit | **0** |
| UEFI Validator Exit | **0** |
| `-e` Ziel | ISO-intern `boot/grub/efi.img` |
| `-append_partition` Ziel | absoluter Host-Pfad `$WORK/efi.img` (Debug: `ESP_APPEND_HOST=`) |
| BOOTX64.EFI | vorhanden |
| BIOS El Torito | isolinux weiter im Report |
| USB | **nicht** geschrieben |

## Entscheidung

| Validator | Next Prompt |
|-----------|-------------|
| Exit **0** | `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` |
| Exit ≠ **0** | `RESCUE_UEFI_XORRISO_PATCH_FAILURE_TRIAGE_CONTINUATION` |

## Fehlercodes

| Code | Bedeutung |
|------|-----------|
| `RESCUE-UEFI-PATCH-XORRISO-001` | xorriso extract/repack |
| `RESCUE-UEFI-PATCH-ESP-SIZE-001` | ESP zu klein / El-Torito-Limit |
| `RESCUE-UEFI-PATCH-MKFS-001` | mkfs.vfat |
| `RESCUE-UEFI-PATCH-GRUB-001` | grub-mkstandalone |
