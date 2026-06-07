# RESCUE USB FAT32 ESP Label Fix — Write Prep

**Datum:** 2026-06-07  
**Version:** `1.7.8.1`  
**Prompt:** `RESCUE_USB_FAT32_ESP_LABEL_FIX_AND_WRITE_PREP`

## Problem

`mkfs.vfat -n SETUPHELFER_RESCUE` ist **ungültig** — FAT/VFAT-Volume-Labels sind auf **11 Zeichen** begrenzt (`SETUPHELFER_RESCUE` = 18).

## Fix

| Feld | Wert | Verwendung |
|------|------|------------|
| GPT-Partitionsname | `SETUPHELFER_RESCUE` | `sgdisk -c 1:…` |
| FAT-Volume-Label | `SETUPHELFER` | `mkfs.vfat -F 32 -n SETUPHELFER` |
| ISO-Volume-ID | `SETUPHELFER_RESCUE` | unverändert (ISO9660) |

## Operator-Handoff (echter Write)

```bash
cd /home/volker/piinstaller
STAGING=build/rescue/fat32-esp-staging
TARGET=/dev/sdb

lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN /dev/sdb
# Ultra Line, Serial 24111412110212

udisksctl unmount -b /dev/sdb1 2>/dev/null || true
sync

sudo sgdisk --zap-all "$TARGET"
sudo sgdisk -n 1:0:+4096MiB -t 1:EF00 -c 1:SETUPHELFER_RESCUE "$TARGET"
sudo mkfs.vfat -F 32 -n SETUPHELFER ${TARGET}1

MNT=$(mktemp -d)
sudo mount ${TARGET}1 "$MNT"
sudo rsync -r --delete --info=progress2 --no-owner --no-group --no-perms --omit-dir-times --exclude='.sqtmp/' "${STAGING}/" "$MNT/"
sync
sudo umount "$MNT"
rmdir "$MNT"

sync
sudo partprobe "$TARGET" || true
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

## Dry-run (1.7.8.1)

- `gpt_partition_name`: SETUPHELFER_RESCUE
- `fat_volume_label`: SETUPHELFER
- `write_executed`: false
- `safety.blocked`: false (bei /dev/sdb Ultra Line)

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_WRITE_OPERATOR_COMPLETION`

## Nicht ausgeführt

Kein sgdisk, mkfs, dd, USB-Write, MSI-Test.
