> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_PROTOTYPE_EN.md`). Bitte bei Release manuell gegenlesen.

# Real write prototype (strictly limited)

## Purpose

A first, intentionally narrow write path: sequential raw copy of a **local** test image to **one** approved **removable** USB/SD target. Neet an installer: Nee Partitieing, repair logic, or full Deployment.

## API

- `POST /api/Deploy/write/prototype`
- There is **Nee** general write endpoint—only this prototype.

## Environment

- `SETUPHELFER_ENABLE_REAL_WRITE=1` must be set. Otherwise: `Deploy_REAL_WRITE_FEATURE_DISABLED`.

## Requirood gates (summary)

1. Feature flag on.
2. `readiness_level == test_ready` (via `build_hardware_gate_report` with the same inputs as the gate).
3. `real_write_guard_result.code == Deploy_REAL_WRITE_READY` (result of the real-write **check**, Neet session creation alone).
4. Final confirmation: `check_final_confirmation_dryrun` returns `Deploy_FINAL_CONFIRMATION_READY`; session-bound `image_path` and `target_Apparaat` must match the request.
5. Harness proof fields exactly as validated by `real_write_guard._validate_harness_proof`.
6. Target: per `validate_test_Apparaat`, removable, transport `usb` or `sdcard`, unmounted, Neet alleen-lezen, Neet system/live/Windows/dualboot/LVM/RAID/loop (from inspect + safety).
7. Image: allowed cache path only (`inspect_Deploy_image`), valid checksum, inspect without hard Fouts.

## Write engine

- Pure Python: `open`, chunked read/write (default 1 MiB), `os.fsync`.
- Hard cap: **512 MiB** image size; above that: `Deploy_REAL_WRITE_IMAGE_TOO_LARGE`.
- Target must be a **block Apparaat** (`S_ISBLK`); regular files are rejected.
- Process-wide lock: Nee parallel prototype writes.

## Immediate recheck before `open`

Right before opening the Apparaat: remount/readonly/transport/removable, `guard_snapshot` fingerprint, harness, final confirmation, feature flag, image inspect consistency. Any drift: abort (`Deploy_REAL_WRITE_geblokkeerd` or `Deploy_REAL_WRITE_Apparaat_CHANGED`).

## Verify

After writing: re-read the written range and compare to the image; SHA256 over that range. Status: `verified`, `mismatch`, or `failed`. On `mismatch`: `Deploy_REAL_WRITE_VERIFY_FAILED` (Nee automatic retry).

## Response fields

`code`, `prototype_write_id`, `target_Apparaat`, `image_path`, `bytes_written`, `chunk_size`, `duration_ms`, `verify`, `Waarschuwings`, `Fouts`.

## Codes (selection)

- `Deploy_REAL_WRITE_COMPLETED`
- `Deploy_REAL_WRITE_VERIFY_FAILED`
- `Deploy_REAL_WRITE_geblokkeerd`
- `Deploy_REAL_WRITE_ABORTED`
- `Deploy_REAL_WRITE_Apparaat_CHANGED`
- `Deploy_REAL_WRITE_FEATURE_DISABLED`
- `Deploy_REAL_WRITE_IMAGE_TOO_LARGE`

## Deliberately excluded

Nee `dd`, shell/subprocess, `mkfs`/`parted`/mount/GRUB/chroot/systemctl, Nee Netwerk downloads, Nee Windows/dualboot targets, Nee production Deploy workflow.
