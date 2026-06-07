# RESCUE USB FAT32 ESP Writer — Dry-Run Result

**Datum:** 2026-06-07  
**Version:** `1.7.8.0`

## Ergebnis

| Prüfung | Ergebnis |
|---------|----------|
| `build-fat32-esp-usb-layout.sh` | Exit **0** |
| `write-fat32-esp-rescue-usb.sh --dry-run` | Exit **0** |
| Echte Schreibausführung | **nein** (`write_executed=false`) |
| Unit-Tests | **14/14 OK** |
| `bash -n` | OK |

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |

## Staging

Pfad: `build/rescue/fat32-esp-staging/`

- EFI/BOOT/BOOTX64.EFI
- boot/grub/grub.cfg (7 menuentry)
- live/vmlinuz, initrd.img, filesystem.squashfs
- setuphelfer/rescue/boot-branding.txt, version.json, evidence.json

## Dry-Run Ziel

`/dev/sdb` — selectable=true, Safety nicht blockiert im dry-run Modus.

Confirm-Phrase für echten Write: `WRITE SETUPHELFER FAT32 ESP USB`

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_WRITE_OPERATOR_RUN`
