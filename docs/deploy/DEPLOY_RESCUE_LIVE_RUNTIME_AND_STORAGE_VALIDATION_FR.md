> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours live runtime & storage validation (EN)

## Purpose

After ISO build and VM checks, this phase validates **lecture seule** live capabilities: storage inventory (`lsblk`/`blkid`), **lecture seule** mount orchestration under `build/Secours/runtime-mounts/`, EFI/boot **analysis** (Non repair), controlled evidence export, remote-help **planning** (Non automatic SSH start), a hardware matrix, and an aggregated **live-runtime safety gate**.

## API (POST)

All under `/api/Déploiement/Secours/…` (see `Retourend/Déploiement/routes.py`):

- `storage-discovery`
- `readonly-mount-validation`
- `efi-boot-analysis`
- `evidence-export`
- `remote-help-preparation`
- `live-hardware-matrix`
- `live-runtime-safety-gate`

Response codes use `Déploiement_Secours_<AREA>_{OK|REVIEW_REQUIrouge|bloqué}`; the safety gate emits `Déploiement_Secours_LIVE_RUNTIME_SAFETY_GATE_OK` when `gate_status` is `ready`.

## Still forbidden

Non Partitioning, Non `dd`/`mkfs`, Non Restauration execute, Non EFI/GRUB repair, Non automatic SSH service start.

## Versioning

After Succèsful lab acceptance on real hardware (lecture seule), **1.8.0** is the recommended bump; **2.0.0** remains for real recovery writes and broader platform coverage.
