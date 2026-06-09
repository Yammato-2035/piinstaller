# RS-001 FAT32 ESP Live Payload Update — Result

**Datum:** 2026-06-09  
**Git HEAD:** `6f3c783`  
**Version:** `1.7.9.3`  
**RS-001:** yellow (kein Fake-Green)

---

## Zusammenfassung

| Feld | Wert |
|------|------|
| Controlled ISO Build | **blocked** (`blocked_requires_operator_sudo_policy`, Exit 30) |
| Workspace-Repack SquashFS | **vorhanden**, Fix verifiziert |
| Alter SquashFS (Stick/ISO-Binary) | `921c3e23bfbeb99a6295b80be5f8b5d40b55994019b0e614fef633138c6bdfe7` |
| Neuer SquashFS (Repack) | `ac95ebc3bdc4693da56d51cda1bb3f5fd36dc68d18b2ff1e8f76aad30a85f00a` |
| `contains_live_medium_fix` | **true** |
| Payload-Update auf `/dev/sdb` | **nicht ausgeführt** (Build-Gate + kein `--execute-update` in Agent-Umgebung) |
| Safety-Probe `/dev/sdb` | **grün** (USB, vfat, SETUPHELFER, EFI System, Serial `24111412110686`) |
| Unit-Tests | **11/11 OK** |

---

## Diagnose (unverändert)

- Stick bootet bis Setuphelfer-Dialog, zeigt aber noch **„Live-Medium nicht stabil“** wegen alter SquashFS.
- Fix `setuphelfer-rescue-live-medium-check.py` liegt im Build-Tree und im Repack-Artefakt, **nicht** auf dem Stick.

---

## Operator — nächster Schritt (Payload only)

**Option A (empfohlen):** Controlled Build im Operator-Terminal, dann Payload-Update:

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
NEW_SQUASHFS="$(find build/rescue/live-build/setuphelfer-rescue-live -type f -name filesystem.squashfs | head -1)"
```

**Option B (aktueller Repack-Fallback):**

```bash
NEW_SQUASHFS="/home/volker/piinstaller/build/rescue/filesystem.squashfs.repacked-1.7.9.3"
```

**Payload-Update (kein Partition-Rewrite):**

```bash
export USB_DEVICE=/dev/sdb
./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target "$USB_DEVICE" \
  --new-squashfs "$NEW_SQUASHFS" \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update

./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_DEVICE"
```

Danach Hardware-Retest gemäß `RS_001_LIVE_MEDIUM_RETEST_HANDOFF.md`.

---

## Evidence

- `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
- `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_latest.json`
- Skript: `scripts/rescue-live/update-fat32-esp-live-payload.sh`
- Tests: `backend/tests/test_rescue_fat32_esp_payload_update_v1.py`
