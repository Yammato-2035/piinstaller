# RS-001 FAT32 ESP Live Payload Update — Result

**Datum:** 2026-06-09 (aktualisiert nach False-Success-Fix)  
**Git HEAD:** `aeee57c` → Fix-Lauf pending  
**Version:** `1.7.9.4`  
**RS-001:** yellow — **kein Fake-Green**

---

## Zusammenfassung

| Feld | Wert |
|------|------|
| Operator-Payload-Update (`20260609_165016`) | **failed** (false success korrigiert) |
| Stick SquashFS (forensic) | **alt** `921c3e23…` |
| Repack-Artefakt | `ac95ebc3…` (Fix enthalten) |
| `ready_for_operator_retest` | **false** |
| Skript-Fix | `update-fat32-esp-live-payload.sh` + Verify-Hash-Gate |

---

## False-Success-Vorfall

Der Lauf `fat32_esp_payload_update_20260609_165016` meldete fälschlich Erfolg. Analyse:  
`docs/evidence/rescue/RS_001_FAT32_ESP_PAYLOAD_UPDATE_FAILURE_ANALYSIS.md`

**Ursachen:**

- Root-owned FAT-Mount: `mkdir`/`cp`/`mv` ohne `sudo`
- `python | tee` maskierte `PermissionError` bei `evidence.json`
- Verify prüfte keinen SquashFS-Hash

---

## Operator — nächster Schritt (nach Skript-Fix)

```bash
export USB_DEVICE=/dev/sdb
NEW_SQUASHFS="/home/volker/piinstaller/build/rescue/filesystem.squashfs.repacked-1.7.9.3"

./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target "$USB_DEVICE" \
  --new-squashfs "$NEW_SQUASHFS" \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh \
  --target "$USB_DEVICE" \
  --expected-squashfs-sha256 ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a
```

**Erst danach** Hardware-Retest gemäß `RS_001_LIVE_MEDIUM_RETEST_HANDOFF.md`.

---

## Evidence

- `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_latest.json`
- `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260609_165016/`
- `docs/evidence/rescue/RS_001_FAT32_ESP_PAYLOAD_UPDATE_FAILURE_ANALYSIS.md`
