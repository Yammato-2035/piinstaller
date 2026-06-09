# RS-001 HW-Boot Phase 3 — Ergebnis

**Datum:** 2026-06-08  
**HEAD vorher:** `158b9da`  
**Branch:** `main`  
**Phase:** Live-Medium-Check Triage + FAT32-ESP Fix (Workspace)

---

## Ziel

Hardware-Boot bis Setuphelfer-Dialog dokumentieren; Live-Medium-Warnung analysieren; Check für FAT32-ESP erweitern — **ohne** USB-Write, ISO-Build, Runtime-Deploy.

---

## Operator-Befund (gelb)

```
USB Write: success
USB Verify: success
UEFI Boot Path: reached
GRUB visible: yes
Setuphelfer dialog visible: yes
Warning: Live-Medium nicht stabil
Repair/install allowed: no
RS-001 status: yellow
```

---

## Root cause (Workspace)

| Item | Detail |
|------|--------|
| Warning source | `setuphelfer-rescue-start-assistant` → `_step_media()` |
| Check script | `setuphelfer-rescue-media-check` → `setuphelfer-rescue-live-medium-check.py` |
| Legacy assumption | SquashFS only at `/run/live/medium/live/filesystem.squashfs` |
| FAT32-ESP reality | Medium also at `/media/*/SETUPHELFER` with surface `setuphelfer/rescue/evidence.json` |
| Diagnosis | `live_medium_check_false_negative_for_verified_fat32_esp` + `fat32_esp_live_mount_path_mismatch` |

---

## Fix (Workspace)

- New `setuphelfer-rescue-live-medium-check.py`: multi-path squashfs resolution, FAT32-ESP evidence + hash gate
- ISO hybrid path unchanged (read + spot checks only)
- Tests: `backend/tests/test_rescue_live_medium_check_v1.py` (8 cases)

---

## Blocker für grün

Squashfs on stick still contains **old** media-check until ISO rebuild + squashfs refresh on medium.  
`ready_for_operator_retest: true` after squashfs with fix is on stick.

---

## RS-001

| Status | yellow |
| Reason | HW boot + dialog OK; live-medium stability blocks |
