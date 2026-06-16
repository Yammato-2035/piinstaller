# R.5B — USB Verify

**Datum:** 2026-06-13

## Status

**Verify nicht ausgeführt** — kein Post-Write-Stick (Write blockiert).

## Geplante Prüfungen (nach Write)

| Check | Methode |
|-------|---------|
| Partitionstabelle GPT | `verify-fat32-esp-rescue-usb.sh` |
| FAT32/ESP | PARTTYPE EF00, FSTYPE vfat |
| `EFI/BOOT/BOOTX64.EFI` | mount + test -f |
| `boot/grub/grub.cfg` | mount + test -f |
| `boot/grub/themes/setuphelfer/theme.txt` | mount + test -f |
| `live/filesystem.squashfs` | mount + sha256 optional |
| `setuphelfer-evidence/` | Verzeichnisstruktur |
| Rescue UI / R.3/R.4 Scripts | SquashFS-Inhalt oder FAT-Layout |

## Operator-Befehl (Referenz)

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_TARGET"
```
