# Real write prototype (strictly limited)

## Purpose

A first, intentionally narrow write path: sequential raw copy of a **local** test image to **one** approved **removable** USB/SD target. Not an installer: no partitioning, repair logic, or full deployment.

## API

- `POST /api/deploy/write/prototype`
- There is **no** general write endpoint—only this prototype.

## Environment

- `SETUPHELFER_ENABLE_REAL_WRITE=1` must be set. Otherwise: `DEPLOY_REAL_WRITE_FEATURE_DISABLED`.

## Required gates (summary)

1. Feature flag on.
2. `readiness_level == test_ready` (via `build_hardware_gate_report` with the same inputs as the gate).
3. `real_write_guard_result.code == DEPLOY_REAL_WRITE_READY` (result of the real-write **check**, not session creation alone).
4. Final confirmation: `check_final_confirmation_dryrun` returns `DEPLOY_FINAL_CONFIRMATION_READY`; session-bound `image_path` and `target_device` must match the request.
5. Harness proof fields exactly as validated by `real_write_guard._validate_harness_proof`.
6. Target: per `validate_test_device`, removable, transport `usb` or `sdcard`, unmounted, not read-only, not system/live/Windows/dualboot/LVM/RAID/loop (from inspect + safety).
7. Image: allowed cache path only (`inspect_deploy_image`), valid checksum, inspect without hard errors.

## Write engine

- Pure Python: `open`, chunked read/write (default 1 MiB), `os.fsync`.
- Hard cap: **512 MiB** image size; above that: `DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE`.
- Target must be a **block device** (`S_ISBLK`); regular files are rejected.
- Process-wide lock: no parallel prototype writes.

## Immediate recheck before `open`

Right before opening the device: remount/readonly/transport/removable, `guard_snapshot` fingerprint, harness, final confirmation, feature flag, image inspect consistency. Any drift: abort (`DEPLOY_REAL_WRITE_BLOCKED` or `DEPLOY_REAL_WRITE_DEVICE_CHANGED`).

## Verify

After writing: re-read the written range and compare to the image; SHA256 over that range. Status: `verified`, `mismatch`, or `failed`. On `mismatch`: `DEPLOY_REAL_WRITE_VERIFY_FAILED` (no automatic retry).

## Response fields

`code`, `prototype_write_id`, `target_device`, `image_path`, `bytes_written`, `chunk_size`, `duration_ms`, `verify`, `warnings`, `errors`.

## Codes (selection)

- `DEPLOY_REAL_WRITE_COMPLETED`
- `DEPLOY_REAL_WRITE_VERIFY_FAILED`
- `DEPLOY_REAL_WRITE_BLOCKED`
- `DEPLOY_REAL_WRITE_ABORTED`
- `DEPLOY_REAL_WRITE_DEVICE_CHANGED`
- `DEPLOY_REAL_WRITE_FEATURE_DISABLED`
- `DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE`

## Deliberately excluded

No `dd`, shell/subprocess, `mkfs`/`parted`/mount/GRUB/chroot/systemctl, no network downloads, no Windows/dualboot targets, no production deploy workflow.
