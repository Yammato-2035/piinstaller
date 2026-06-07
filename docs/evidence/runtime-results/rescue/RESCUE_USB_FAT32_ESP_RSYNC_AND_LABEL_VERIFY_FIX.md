# RESCUE USB FAT32 ESP — rsync & Label Verify Fix

**Datum:** 2026-06-07  
**Version:** `1.7.8.2`  
**Prompt:** `RESCUE_USB_FAT32_ESP_RSYNC_AND_LABEL_VERIFY_FIX`

## Root Cause (Operator-Lauf)

1. **`rsync -a`** auf FAT32 — Archive-Modus versucht Owner/Group/Permissions zu setzen; FAT32 unterstützt das nicht.
2. **Label-Verify** — `blkid` ohne `-p` lieferte `BLKID_LABEL=` (Cache/Timing); Verify brach mit Exit 22 ab.

## Fixes

| Bereich | Änderung |
|---------|----------|
| Copy | `rsync -r --delete --info=progress2 --no-owner --no-group --no-perms --omit-dir-times --exclude='.sqtmp/'` |
| Post-sgdisk | `partprobe`, `udevadm settle`, kurze Wartezeit |
| Post-mkfs | vfat-Check, `blkid -p`, `fatlabel`/`dosfslabel`-Fallback |
| Verify | `blkid -p`, `fatlabel`/`dosfslabel`-Fallback, GPT-Name Pflicht, Reparaturhinweis |
| Staging | `.sqtmp/` nach Extract entfernt + vom Copy ausgeschlossen |

## Operator-Handoff (korrigiert)

```bash
cd /home/volker/piinstaller
STAGING=build/rescue/fat32-esp-staging
TARGET=/dev/sdb

lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN "$TARGET"
udisksctl unmount -b ${TARGET}1 2>/dev/null || true
sync

sudo sgdisk --zap-all "$TARGET"
sudo sgdisk -n 1:0:+4096MiB -t 1:EF00 -c 1:SETUPHELFER_RESCUE "$TARGET"
sync
sudo partprobe "$TARGET" || true
sudo udevadm settle --timeout=30 || true
sleep 2

sudo mkfs.vfat -F 32 -n SETUPHELFER ${TARGET}1
sync
sudo partprobe "$TARGET" || true
sudo udevadm settle --timeout=30 || true
sleep 1

FSTYPE=$(lsblk -no FSTYPE "${TARGET}1" | head -1)
[[ "$FSTYPE" == "vfat" ]] || { echo "ERROR: ${TARGET}1 not vfat ($FSTYPE)"; exit 1; }
LABEL=$(blkid -p -s LABEL -o value "${TARGET}1" 2>/dev/null || true)
if [[ "$LABEL" != "SETUPHELFER" ]]; then
  sudo fatlabel ${TARGET}1 SETUPHELFER 2>/dev/null || sudo dosfslabel ${TARGET}1 SETUPHELFER
fi

MNT=$(mktemp -d)
sudo mount ${TARGET}1 "$MNT"
sudo rsync -r --delete --info=progress2 --no-owner --no-group --no-perms --omit-dir-times --exclude='.sqtmp/' "${STAGING}/" "$MNT/"
sync && sudo umount "$MNT" && rmdir "$MNT"
sync && sudo partprobe "$TARGET" || true
sudo udevadm settle --timeout=30 || true

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

**Hinweis:** FAT32 speichert keine Unix-Owner/Groups/Permissions.

## Dry-run

Siehe Abschlussbericht — `staging_copy_command` mit FAT-safe rsync, `write_executed=false`.

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_WRITE_OPERATOR_COMPLETION_AFTER_RSYNC_FIX`

## Nicht ausgeführt

Kein sgdisk, mkfs, dd, USB-Write, MSI-Test, Push.
