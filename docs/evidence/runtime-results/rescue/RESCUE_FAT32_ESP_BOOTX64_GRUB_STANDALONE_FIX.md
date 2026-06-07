# RESCUE FAT32 ESP — Standalone GRUB BOOTX64 Fix

**Datum:** 2026-06-07  
**Version:** `1.7.8.6`  
**Prompt:** `RESCUE_FAT32_ESP_BOOTX64_GRUB_STANDALONE_FIX`

## MSI-Befund

Interaktive GRUB-Konsole am MSI:

```text
grub> ls
(proc) (memdisk) (hd0) (hd1) (hd2)
```

Kein `(hdX,gpt1)` — GRUB sieht Laufwerke, aber **keine GPT/FAT-Partitionen**.  
Folge: `error: file '/live/vmlinuz' not found` — Root-Problem in BOOTX64.EFI, nicht fehlendes vmlinuz auf dem Stick.

## Root Cause

`EFI/BOOT/BOOTX64.EFI` wurde **blind aus der ISO** extrahiert. Diese GRUB-EFI-Build ist für **ISO/El-Torito/isohybrid** (iso9660-Module, file-search), nicht für **native FAT32-ESP auf GPT**. Fehlende `part_gpt`/`fat`-Module → keine Partitionssicht.

## Fix 1.7.8.6

| Vorher | Nachher |
|--------|---------|
| ISO `/EFI/BOOT/BOOTX64.EFI` kopieren | `grub-mkstandalone -O x86_64-efi` |
| Embedded: iso9660/file search | Embedded: `insmod part_gpt`, `insmod fat`, `search_label`, `configfile` |
| Kein Manifest | `bootx64_source=grub_mkstandalone` in evidence.json |

Neues Skript: `scripts/rescue-live/build-fat32-esp-bootx64.sh`

Embedded Bootstrap lädt externe `boot/grub/grub.cfg` (UUID per `patch-fat32-esp-grub-for-uuid.sh` nach mkfs).

### Staging-Verifikation

| Feld | Wert |
|------|------|
| bootx64_source | grub_mkstandalone |
| staging BOOTX64 SHA256 | `1f1bb10cec710fefd10f628060d3d961d4a47dfa0ec655c967059336e3f6a4c7` |
| ISO BOOTX64 SHA256 | `8656837e2f3ac643ca86931bf5419885bcfc0cbdfe75b087382c768b04fc81db` |
| bootx64_differs_from_iso | **true** |
| BOOTX64 size | 3657728 bytes |

### Host-Tooling

`grub-mkstandalone` **verfügbar** (GRUB 2.12-1ubuntu7.3).  
Falls fehlend: `sudo apt install grub-efi-amd64-bin grub-common` — Exit 25, kein Fake-Green.

## Operator-Handoff (Recopy only)

```bash
cd /home/volker/piinstaller
rm -rf build/rescue/fat32-esp-staging
./scripts/rescue-live/build-fat32-esp-usb-layout.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --output-dir build/rescue/fat32-esp-staging

# Optional nach mkfs wenn UUID in grub.cfg gewünscht:
# FAT_UUID=$(sudo blkid -p -s UUID -o value /dev/sdb1)
# ./scripts/rescue-live/patch-fat32-esp-grub-for-uuid.sh --staging build/rescue/fat32-esp-staging --fat-uuid "$FAT_UUID"

MNT=$(mktemp -d)
sudo mount /dev/sdb1 "$MNT"
sudo rsync -r --delete --info=progress2 --no-owner --no-group --no-perms \
  --omit-dir-times --exclude='.sqtmp/' build/rescue/fat32-esp-staging/ "$MNT/"
sync && sudo umount "$MNT" && rmdir "$MNT"

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

Kein mkfs/sgdisk nötig wenn FAT32-ESP bereits ok.

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_BOOTX64_FIXED_RECOPY_OPERATOR_RUN`

Bei fehlendem grub-mkstandalone: `RESCUE_HOST_GRUB_EFI_TOOLING_INSTALL_OPERATOR_RUN`

## Nicht ausgeführt

Kein USB-Write durch Agent, kein ISO-Rebuild, kein MSI-Test.
