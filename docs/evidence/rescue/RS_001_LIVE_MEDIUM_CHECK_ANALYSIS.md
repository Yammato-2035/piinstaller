# RS-001 Live-Medium Check Analysis

**Date:** 2026-06-08  
**Diagnosis:** `live_medium_check_false_negative_for_verified_fat32_esp`  
**Secondary:** `fat32_esp_live_mount_path_mismatch`

---

## Warning source

| Component | Path |
|-----------|------|
| Dialog | `scripts/rescue-live/image/setuphelfer-rescue-start-assistant` (`_step_media`, lines ~110–125) |
| Check | `scripts/rescue-live/image/setuphelfer-rescue-media-check` |
| Logic (new) | `scripts/rescue-live/image/setuphelfer-rescue-live-medium-check.py` |

Trigger: `live_media_runtime_stable != true` in `/run/setuphelfer-rescue/media-check.json`.

---

## Legacy check conditions (pre-fix)

| Condition | Result if fail |
|-----------|----------------|
| `setuphelfer_rescue_is_live()` | `NOT_RESCUE_LIVE` |
| SquashFS at `/run/live/medium/live/filesystem.squashfs` readable | `SQUASHFS_PATH_MISSING` / `SQUASHFS_READ_IO_ERROR` |
| unsquashfs spot paths inside squashfs | `SQUASHFS_SPOT_CHECK_FAILED` |
| FAT32 surface evidence / hash | **not evaluated** |

---

## FAT32-ESP stick evidence (verified write)

| Artifact | Status |
|----------|--------|
| `EFI/BOOT/BOOTX64.EFI` | present (verify.log) |
| `boot/grub/grub.cfg` | present |
| `live/vmlinuz` | present |
| `live/initrd.img` | present |
| `live/filesystem.squashfs` | present (~555958272 bytes) |
| `setuphelfer/rescue/evidence.json` | present (writer_mode `fat32_esp`) |
| `setuphelfer/rescue/version.json` | present |
| `setuphelfer/rescue/boot-branding.txt` | present |
| FAT label `SETUPHELFER` | verified |
| GPT name `SETUPHELFER_RESCUE` | verified |
| FAT UUID `C9C8-394A` | verified |

---

## Comparison table

| Prüfschritt | Erwartung des Checks (alt) | FAT32-ESP Ist | Status (alt) | Schlussfolgerung |
|-------------|---------------------------|---------------|--------------|------------------|
| Live boot detected | cmdline `boot=live` / `/run/live/medium` | yes (HW boot) | ok | — |
| SquashFS path | `/run/live/medium/live/filesystem.squashfs` | file on FAT ESP; mount often `/media/*/SETUPHELFER` | **fail** | Path mismatch → false negative |
| SquashFS read | `dd` full read | file intact (USB verify) | likely ok if path found | — |
| Spot checks | unsquashfs paths in squashfs | squashfs content from ISO extract | ok if path found | — |
| Surface evidence.json | not checked | `writer_mode=fat32_esp` + file SHA256 list | ignored | Missing gate for FAT32-ESP |
| SquashFS hash vs evidence | not checked | SHA in `evidence.json` `files[]` | ignored | Fix adds hash compare |
| Required FAT files | not checked | all present per verify.log | ignored | Fix adds surface file gate |
| Repair block when unstable | whiptail + plan builder | observed on HW | ok | Safety preserved |

---

## Fix summary

1. Resolve squashfs from `/run/live/medium`, `/lib/live/mount/medium`, `/media/*/SETUPHELFER`
2. Detect `fat32_esp` via `setuphelfer/rescue/evidence.json`
3. Require surface files + squashfs SHA256 match for `fat32_esp`
4. Keep ISO hybrid behavior (squashfs read/spot only)

---

## RS-001

**yellow** — not green until HW boot without “Live-Medium nicht stabil” warning.
