# RS-001 Live-Medium Retest — Operator Handoff

**Date:** 2026-06-09  
**RS-001:** yellow  
**ready_for_operator_retest:** **false**

---

## Blocker

Der Payload-Update-Lauf `fat32_esp_payload_update_20260609_165016` meldete fälschlich Erfolg.  
Stick enthält nachweislich noch die **alte** SquashFS (`921c3e23…`).

**Hardware-Retest ist gesperrt**, bis ein erneuter Payload-Update-Lauf mit dem **fixierten** Skript den neuen Hash (`ac95ebc3…`) auf dem Stick belegt.

Analyse: `docs/evidence/rescue/RS_001_FAT32_ESP_PAYLOAD_UPDATE_FAILURE_ANALYSIS.md`

---

## Ziel (nach erfolgreichem Payload-Update)

Erneuter Hardware-Boot mit FAT32-ESP-Stick (`/dev/sdb`, UUID `C9C8-394A`) — Warnung „Live-Medium nicht stabil“ darf **nicht** mehr erscheinen.

---

## Schritt 1 — Payload-Update (Operator, fixiertes Skript)

```bash
export USB_DEVICE=/dev/sdb
NEW_SQUASHFS="/home/volker/piinstaller/build/rescue/filesystem.squashfs.repacked-1.7.9.3"

./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target "$USB_DEVICE" \
  --new-squashfs "$NEW_SQUASHFS" \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update
```

Erwartung in `result.json`:

- `payload_update_status: success`
- `stick_squashfs_hash_ok: true`
- `stick_squashfs_sha256` == `ac95ebc3…`

---

## Schritt 2 — Verify mit Hash-Gate

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh \
  --target /dev/sdb \
  --expected-squashfs-sha256 ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a
```

---

## Schritt 3 — Hardware-Retest (erst nach Schritt 1+2 grün)

1. UEFI-Bootmenü zeigt Stick
2. GRUB erscheint
3. „Setuphelfer Rettung starten“ startet
4. **Keine** Warnung „Live-Medium nicht stabil“
5. Setuphelfer-Menü/TUI erscheint
6. Optional: `cat /run/setuphelfer-rescue/media-check.json`

---

## RS-001 grün nur wenn

Setuphelfer-Menü/TUI **ohne** Live-Medium-Warnung erreicht wird.
