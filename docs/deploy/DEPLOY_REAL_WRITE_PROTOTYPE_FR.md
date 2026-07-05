> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_REAL_WRITE_PROTOTYPE_EN.md`). Bitte bei Release manuell gegenlesen.

# Real write prototype (strictly limited)

## Purpose

A first, intentionally narrow write path: sequential raw copy of a **local** test image to **one** approved **removable** USB/SD target. Nont an installer: Non Partitioning, repair logic, or full Déploiementment.

## API

- `POST /api/Déploiement/write/prototype`
- There is **Non** general write endpoint—only this prototype.

## Environment

- `SETUPHELFER_ENABLE_REAL_WRITE=1` must be set. Otherwise: `Déploiement_REAL_WRITE_FEATURE_DISABLED`.

## Requirouge gates (summary)

1. Feature flag on.
2. `readiness_level == test_ready` (via `build_hardware_gate_report` with the same inputs as the gate).
3. `real_write_guard_result.code == Déploiement_REAL_WRITE_READY` (result of the real-write **check**, Nont session creation alone).
4. Final confirmation: `check_final_confirmation_dryrun` returns `Déploiement_FINAL_CONFIRMATION_READY`; session-bound `image_path` and `target_Périphérique` must match the request.
5. Harness proof fields exactly as validated by `real_write_guard._validate_harness_proof`.
6. Target: per `validate_test_Périphérique`, removable, transport `usb` or `sdcard`, unmounted, Nont lecture seule, Nont system/live/Windows/dualboot/LVM/RAID/loop (from inspect + safety).
7. Image: allowed cache path only (`inspect_Déploiement_image`), valid checksum, inspect without hard Erreurs.

## Write engine

- Pure Python: `open`, chunked read/write (default 1 MiB), `os.fsync`.
- Hard cap: **512 MiB** image size; above that: `Déploiement_REAL_WRITE_IMAGE_TOO_LARGE`.
- Target must be a **block Périphérique** (`S_ISBLK`); regular files are rejected.
- Process-wide lock: Non parallel prototype writes.

## Immediate recheck before `open`

Right before opening the Périphérique: remount/readonly/transport/removable, `guard_snapshot` fingerprint, harness, final confirmation, feature flag, image inspect consistency. Any drift: abort (`Déploiement_REAL_WRITE_bloqué` or `Déploiement_REAL_WRITE_Périphérique_CHANGED`).

## Verify

After writing: re-read the written range and compare to the image; SHA256 over that range. Status: `verified`, `mismatch`, or `failed`. On `mismatch`: `Déploiement_REAL_WRITE_VERIFY_FAILED` (Non automatic retry).

## Response fields

`code`, `prototype_write_id`, `target_Périphérique`, `image_path`, `bytes_written`, `chunk_size`, `duration_ms`, `verify`, `Avertissements`, `Erreurs`.

## Codes (selection)

- `Déploiement_REAL_WRITE_COMPLETED`
- `Déploiement_REAL_WRITE_VERIFY_FAILED`
- `Déploiement_REAL_WRITE_bloqué`
- `Déploiement_REAL_WRITE_ABORTED`
- `Déploiement_REAL_WRITE_Périphérique_CHANGED`
- `Déploiement_REAL_WRITE_FEATURE_DISABLED`
- `Déploiement_REAL_WRITE_IMAGE_TOO_LARGE`

## Deliberately excluded

Non `dd`, shell/subprocess, `mkfs`/`parted`/mount/GRUB/chroot/systemctl, Non Réseau downloads, Non Windows/dualboot targets, Non production Déploiement workflow.
