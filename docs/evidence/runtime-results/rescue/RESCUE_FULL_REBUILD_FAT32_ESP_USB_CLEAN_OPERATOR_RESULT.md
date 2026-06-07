# RESCUE Full Rebuild FAT32 ESP USB — Clean Operator Run

**Datum:** 2026-06-07  
**Version:** `1.7.8.5`  
**Prompt:** `RESCUE_FULL_REBUILD_FAT32_ESP_USB_CLEAN_OPERATOR_RUN`  
**HEAD (Start):** `fe03ae3`  
**HEAD (Ende):** siehe Commit unten

## Ergebnis

**Kein vollständiger Operator-Write durch Agent** — sudo/interaktives Terminal erforderlich.  
**Code-Fix 1.7.8.5:** GRUB patch mit echter **FAT-UUID** nach mkfs (vor rsync).  
**MSI-Boot:** **nicht freigegeben** — USB muss im Operator-Terminal neu aufgebaut werden.

| Phase | Ergebnis |
|-------|----------|
| 0 Sicherheitsgate | **grün** — `/dev/sdb` Ultra Line, Serial `24111412110212`, usb |
| 1 ISO Clean Build | **Agent blockiert** (sudo Passwort) — bestehende ISO UEFI-validiert |
| 2 SquashFS-Inhalt | **grün** auf bestehender ISO |
| 3 Staging neu | **grün** (frisch aus ISO) |
| 4 GRUB Staging | **grün** — label + UUID-Patch-Tool |
| 5–7 USB Write | **nicht ausgeführt** (Agent-Policy) |
| 8 Real USB Verify | **nicht grün** — Stick hat alte grub.cfg ohne FAT-UUID |
| 9 QEMU | nicht ausgeführt |
| MSI-Boot-Freigabe | **false** |

## Phase 0

```
Branch: main
VERSION: 1.7.8.5 (nach Fix)
/dev/sdb: Ultra Line, 24111412110212, usb, gpt
/dev/sdb1: vfat, LABEL=SETUPHELFER, PARTLABEL=SETUPHELFER_RESCUE
/dev/sda: Backup — nicht verwendet
```

## Phase 1 — ISO (bestehend, nicht neu gebaut)

| Feld | Wert |
|------|------|
| ISO | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 683671552 bytes |
| SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |
| UEFI-Validator | Exit **0** |
| iso_rebuilt_clean | **false** (Operator muss `RESCUE_FULL_REBUILD_FAT32_ESP_FREIGEGEBEN=1` + sudo rebuild) |

## Phase 2 — SquashFS Pflichtbestandteile (bestehende ISO)

Alle Pflicht-Skripte, nmcli, NetworkManager, rfkill, iw, ping, curl, iwlwifi-9000*, ibt-17-16-1.sfi, regulatory.db — **vorhanden**.

## Root Cause MSI GRUB-Fehler

1. Alte `grub.cfg` auf Stick: nur Label-Search, **keine FAT-UUID** nach mkfs.
2. `search --file /live/filesystem.squashfs` (historisch) — GRUB `$root` falsch auf UEFI/FAT.
3. Verify prüfte Dateien, aber nicht UUID-Konsistenz zwischen blkid und grub.cfg.

## Fix 1.7.8.5

- `patch-fat32-esp-grub-for-uuid.sh` — patcht Staging **nach mkfs**, **vor rsync**
- `grub.cfg` auf Stick:

```grub
search --no-floppy --fs-uuid <FAT_UUID> --set=root
if [ -z "$root" ]; then
  search --no-floppy --label SETUPHELFER --set=root
fi
if [ -z "$root" ]; then
  set root=($cmdpath)
fi
```

- Verify: erwartet `fs-uuid` matching `blkid -p` auf `/dev/sdb1` + Kernel/Initrd-Pfade auf gemountetem Stick

## Operator — Voll-Rebuild (interaktives Terminal)

```bash
cd /home/volker/piinstaller
export RESCUE_FULL_REBUILD_FAT32_ESP_FREIGEGEBEN=1

# Phase 1 — ISO neu (sudo)
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build

ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
sha256sum "$ISO"
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"

# Phase 3 — Staging
rm -rf build/rescue/fat32-esp-staging
./scripts/rescue-live/build-fat32-esp-usb-layout.sh --iso "$ISO" --output-dir build/rescue/fat32-esp-staging

# Phase 5–7 — USB (nur /dev/sdb Ultra Line 24111412110212)
TARGET=/dev/sdb
STAGING=build/rescue/fat32-esp-staging
lsblk -o NAME,MODEL,SERIAL,TRAN "$TARGET"  # prüfen!

udisksctl unmount -b ${TARGET}1 2>/dev/null || true
sync
sudo wipefs --no-act "$TARGET"
sudo wipefs -a "$TARGET"
sudo sgdisk --zap-all "$TARGET"
sudo sgdisk -n 1:0:+4096MiB -t 1:EF00 -c 1:SETUPHELFER_RESCUE "$TARGET"
sync && sudo partprobe "$TARGET" && sudo udevadm settle --timeout=30 && sleep 2
sudo mkfs.vfat -F 32 -n SETUPHELFER ${TARGET}1
sync && sudo partprobe "$TARGET" && sudo udevadm settle --timeout=30 && sleep 2

FAT_UUID=$(sudo blkid -p -s UUID -o value ${TARGET}1)
FAT_LABEL=$(sudo blkid -p -s LABEL -o value ${TARGET}1)
echo "FAT_UUID=$FAT_UUID FAT_LABEL=$FAT_LABEL"

./scripts/rescue-live/patch-fat32-esp-grub-for-uuid.sh --staging "$STAGING" --fat-uuid "$FAT_UUID"

MNT=$(mktemp -d)
sudo mount ${TARGET}1 "$MNT"
sudo rsync -r --delete --info=progress2 --no-owner --no-group --no-perms \
  --omit-dir-times --exclude='.sqtmp/' "${STAGING}/" "$MNT/"
sync && sudo umount "$MNT" && rmdir "$MNT"

# Phase 8
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target /dev/sdb
```

## Gate (ehrlich)

| Feld | Wert |
|------|------|
| iso_rebuilt_clean | false |
| iso_uefi_validated | true (bestehende ISO) |
| fat32_esp_usb_written | false |
| fat32_esp_usb_verified | false |
| usb_stick_layout | vfat auf sdb1 (alter Inhalt) |
| grub_real_usb_kernel_paths_verified | false |
| msi_boot_handoff_ready | **false** |

## Nächster Prompt

`RESCUE_MSI_BOOT_CLEAN_FAT32_ESP_START_ASSISTANT_TELEMETRY_RUN` (nach erfolgreichem Operator-Write + Verify Exit 0)

Bei erneutem GRUB-Fehler: `RESCUE_MSI_GRUB_INTERACTIVE_ROOT_DISCOVERY`

## Nicht ausgeführt

USB wipefs/sgdisk/mkfs/rsync durch Agent, MSI-Boot, Windows-Inspect, Push.
