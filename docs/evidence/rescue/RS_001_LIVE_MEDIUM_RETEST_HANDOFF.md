# RS-001 Live-Medium Retest — Operator Handoff

**Date:** 2026-06-09  
**RS-001:** yellow (pending hardware retest)  
**ready_for_operator_retest:** true (after payload update on stick)

---

## Ziel

Erneuter Hardware-Boot mit **bestehendem** FAT32-ESP-Stick (`/dev/sdb`, UUID `C9C8-394A`) — Warnung „Live-Medium nicht stabil“ darf **nicht** mehr erscheinen.

---

## Aktueller Stand

| Item | Status |
|------|--------|
| USB FAT32-ESP Layout | verified (vorheriger Write+Verify) |
| Live-Medium-Check-Fix im Repo | `6f3c783` / `1.7.9.3` |
| Neues SquashFS-Artefakt (Repack) | `ac95ebc3…` — enthält Fix |
| Stick `live/filesystem.squashfs` | **noch alt** (`921c3e23…`) |
| Payload-Update-Skript | bereit, Tests grün |

---

## Vor dem Retest (Operator)

SquashFS auf Stick aktualisieren — **nur Payload**, kein vollständiger USB-Rewrite:

```bash
export USB_DEVICE=/dev/sdb
NEW_SQUASHFS="/home/volker/piinstaller/build/rescue/filesystem.squashfs.repacked-1.7.9.3"

./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target "$USB_DEVICE" \
  --new-squashfs "$NEW_SQUASHFS" \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_DEVICE"
```

Alternativ: nach Controlled ISO Rebuild den SquashFS-Pfad aus `binary/live/filesystem.squashfs` verwenden.

---

## Nicht in diesem Retest

- kein vollständiger USB-Rewrite / Partitionieren / Formatieren
- kein Backup / Restore / Provisioning
- keine Reparatur / Installation starten

---

## Operator prüft

1. UEFI-Bootmenü zeigt Stick
2. GRUB erscheint
3. Standard-Eintrag „Setuphelfer Rettung starten“ startet
4. Warnung **„Live-Medium nicht stabil“** erscheint **nicht**
5. Setuphelfer-Menü/TUI erscheint
6. Optional: `cat /run/setuphelfer-rescue/media-check.json` → `live_media_runtime_stable: true`
7. **Keine** Reparatur/Installation starten

---

## RS-001 grün nur wenn

Setuphelfer-Menü/TUI **ohne** Live-Medium-Warnung erreicht wird.

---

## Evidence liefern

- Screenshot/Foto Bootmenü + TUI
- `media-check.json` Inhalt
- Kurzbericht in `docs/evidence/rescue/RS_001_PHYSICAL_BOOT_RESULT.md` aktualisieren
