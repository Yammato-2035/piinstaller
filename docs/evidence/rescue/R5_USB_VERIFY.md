# R.5 — USB Verify

## Status

**Nicht ausgeführt** — kein USB-Write in dieser Kampagne.

Nach Write prüfen:

- FAT32/ESP mount read-only wo möglich
- `boot/grub/grub.cfg` Menu-Einträge
- `setuphelfer-evidence/` Verzeichnis vorbereitet (leer oder preload)
- Keine internen NVMe als Ziel beschrieben

Skript: `verify-fat32-esp-rescue-usb.sh`
