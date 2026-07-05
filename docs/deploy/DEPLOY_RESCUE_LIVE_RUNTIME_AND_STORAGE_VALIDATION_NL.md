> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding live runtime & storage validation (EN)

## Purpose

After ISO build and VM checks, this phase validates **alleen-lezen** live capabilities: storage inventory (`lsblk`/`blkid`), **alleen-lezen** mount orchestration under `build/roodding/runtime-mounts/`, EFI/boot **analysis** (Nee repair), controlled evidence export, remote-help **planning** (Nee automatic SSH start), a hardware matrix, and an aggregated **live-runtime safety gate**.

## API (POST)

All under `/api/Deploy/roodding/…` (see `Terugend/Deploy/routes.py`):

- `storage-discovery`
- `readonly-mount-validation`
- `efi-boot-analysis`
- `evidence-export`
- `remote-help-preparation`
- `live-hardware-matrix`
- `live-runtime-safety-gate`

Response codes use `Deploy_roodding_<AREA>_{OK|REVIEW_REQUIrood|geblokkeerd}`; the safety gate emits `Deploy_roodding_LIVE_RUNTIME_SAFETY_GATE_OK` when `gate_status` is `ready`.

## Still forbidden

Nee Partitieing, Nee `dd`/`mkfs`, Nee Herstel execute, Nee EFI/GRUB repair, Nee automatic SSH service start.

## Versioning

After Geslaagdful lab acceptance on real hardware (alleen-lezen), **1.8.0** is the recommended bump; **2.0.0** remains for real recovery writes and broader platform coverage.
