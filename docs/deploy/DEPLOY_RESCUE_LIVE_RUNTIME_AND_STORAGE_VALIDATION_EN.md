# Deploy — Rescue live runtime & storage validation (EN)

## Purpose

After ISO build and VM checks, this phase validates **read-only** live capabilities: storage inventory (`lsblk`/`blkid`), **read-only** mount orchestration under `build/rescue/runtime-mounts/`, EFI/boot **analysis** (no repair), controlled evidence export, remote-help **planning** (no automatic SSH start), a hardware matrix, and an aggregated **live-runtime safety gate**.

## API (POST)

All under `/api/deploy/rescue/…` (see `backend/deploy/routes.py`):

- `storage-discovery`
- `readonly-mount-validation`
- `efi-boot-analysis`
- `evidence-export`
- `remote-help-preparation`
- `live-hardware-matrix`
- `live-runtime-safety-gate`

Response codes use `DEPLOY_RESCUE_<AREA>_{OK|REVIEW_REQUIRED|BLOCKED}`; the safety gate emits `DEPLOY_RESCUE_LIVE_RUNTIME_SAFETY_GATE_OK` when `gate_status` is `ready`.

## Still forbidden

No partitioning, no `dd`/`mkfs`, no restore execute, no EFI/GRUB repair, no automatic SSH service start.

## Versioning

After successful lab acceptance on real hardware (read-only), **1.8.0** is the recommended bump; **2.0.0** remains for real recovery writes and broader platform coverage.
