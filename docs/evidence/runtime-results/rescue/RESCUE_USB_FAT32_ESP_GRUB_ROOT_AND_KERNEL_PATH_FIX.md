# RESCUE USB FAT32 ESP — GRUB Root & Kernel Path Fix

**Datum:** 2026-06-07  
**Version:** `1.7.8.4`  
**Prompt:** `RESCUE_USB_FAT32_ESP_GRUB_ROOT_AND_KERNEL_PATH_FIX`

## Symptom (MSI)

GRUB startet (`BOOTX64.EFI` OK), bricht ab mit:

```text
error: file '/live/vmlinuz' not found.
error: you need to load the kernel first.
```

Pflichtdateien waren auf dem Stick vorhanden — reines Pfad-/Root-Problem in `grub.cfg`.

## Root Cause

Die erzeugte `grub.cfg` nutzte:

```grub
search --set=root --file /live/filesystem.squashfs
```

Das ist ISO/El-Torito-Logik. Auf FAT32-ESP muss GRUB das **FAT-Volume mit Label `SETUPHELFER`** als root setzen — nicht per Dateisuche, die auf UEFI/FAT scheitern kann.

## Fix

Neue Funktion `generate_fat32_esp_grub_cfg()`:

```grub
search --no-floppy --label SETUPHELFER --set=root
if [ -z "$root" ]; then
  set root=($cmdpath)
fi
```

- Keine Suche nach `SETUPHELFER_RESCUE` (ISO/GPT-Name)
- Kein `search --file`, kein loopback/iso-scan
- Kernel/Initrd: `/live/vmlinuz`, `/live/initrd.img`

Verify prüft zusätzlich:

- `RESCUE-FAT32-GRUB-ROOT-001`
- `RESCUE-FAT32-GRUB-KERNEL-PATH-001`
- `RESCUE-FAT32-GRUB-INITRD-PATH-001`

## Operator-Handoff (Recopy only)

**Kein** sgdisk, **kein** mkfs — nur Staging neu kopieren:

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/build-fat32-esp-usb-layout.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --output-dir build/rescue/fat32-esp-staging

STAGING=build/rescue/fat32-esp-staging
TARGET=/dev/sdb
MNT=$(mktemp -d)
sudo mount ${TARGET}1 "$MNT"
sudo rsync -r --delete --info=progress2 --no-owner --no-group --no-perms \
  --omit-dir-times --exclude='.sqtmp/' "${STAGING}/" "$MNT/"
sync && sudo umount "$MNT" && rmdir "$MNT"
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

## Nächster Prompt

`RESCUE_USB_FAT32_ESP_GRUB_FIXED_RECOPY_OPERATOR_RUN`

## Nicht ausgeführt

Kein USB-Write durch Agent, kein MSI-Test, kein Push.
