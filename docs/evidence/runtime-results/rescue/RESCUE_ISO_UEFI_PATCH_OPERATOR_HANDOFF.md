# RESCUE ISO UEFI Patch — Operator Handoff

**Status:** `awaiting_operator_patch_and_validate`  
**Next Prompt nach Validator Exit 0:** `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT`

## Voraussetzungen

- ISO vorhanden nach Controlled Build (`LB_EXIT=0`)
- Patch-Skript-Fix im Workspace (16 MiB ESP via `mkfs.vfat -C`)
- Operator-Terminal mit `sudo` (ISO ist root-owned)
- **Kein** USB-Write in diesem Schritt, bis UEFI-Validator Exit 0

## Operator-Befehle

```bash
cd /home/volker/piinstaller

ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso

ls -lh "$ISO"
sha256sum "$ISO"
file "$ISO"

./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO" || true

# Plan-Vorschau (read-only, kein sudo nötig):
./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --plan-only "$ISO"

sudo ./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place "$ISO"

./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"
sha256sum "$ISO"
file "$ISO"
xorriso -indev "$ISO" -report_el_torito as_mkisofs
xorriso -indev "$ISO" -find /EFI/BOOT/BOOTX64.EFI -type f -print 2>/dev/null || true
```

## Erfolgskriterien

| Check | Erwartung |
|-------|-----------|
| Patch Exit | **0** |
| UEFI Validator Exit | **0** |
| BOOTX64.EFI | vorhanden |
| EFI El Torito | im xorriso-Report sichtbar |
| BIOS/isolinux | weiterhin im Report |
| USB geschrieben | **nein** (nächster Prompt) |

## Bei Fehlschlag

| Exit / Code | Aktion |
|-------------|--------|
| 41 `RESCUE-UEFI-PATCH-ESP-SIZE-001` | ESP-Konstanten prüfen, Skript-Version |
| 42 `RESCUE-UEFI-PATCH-MKFS-001` | `mkfs.vfat`, `mtools` auf Host |
| 43 `RESCUE-UEFI-PATCH-GRUB-001` | `grub-mkstandalone` |
| 44 `RESCUE-UEFI-PATCH-XORRISO-001` | xorriso extract/repack Log |

**Next Prompt bei Validator ≠ 0:** `RESCUE_ISO_UEFI_PATCH_OPERATOR_RUN` (Retry/Triage)
