# Deploy — Rescue runtime assembly pipeline (EN)

## Purpose

Materializes a **composed rescue runtime layout** under `build/rescue/runtime/` (directories, placeholders, JSON manifests, template shell scripts) **without** ISO build, VM boot, or real service starts.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/deploy/rescue/runtime/root` |
| `POST` | `/api/deploy/rescue/runtime/backend` |
| `POST` | `/api/deploy/rescue/runtime/frontend` |
| `POST` | `/api/deploy/rescue/runtime/recovery` |
| `POST` | `/api/deploy/rescue/runtime/offline-config` |
| `POST` | `/api/deploy/rescue/runtime/startup-scripts` |
| `POST` | `/api/deploy/rescue/runtime/final-gate` |
| `POST` | `/api/deploy/rescue/runtime/safety-validation` |

Codes: `DEPLOY_RESCUE_RUNTIME_ROOT_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (same pattern for `RUNTIME_BACKEND`, `RUNTIME_FRONTEND`, `RUNTIME_RECOVERY`, `RUNTIME_OFFLINE_CONFIG`, `RUNTIME_STARTUP_SCRIPTS`, `RUNTIME_SAFETY_VALIDATION`). Final gate: `DEPLOY_RESCUE_RUNTIME_FINAL_GATE_READY` when `gate_status` is `ready`.

## Forbidden actions

No `qemu`, `grub-mkrescue`, `xorriso`, `dd`, `mkfs`, `chroot`, `mount --bind`, no real restore, no `systemctl` orchestration from this pipeline.

## Final gate inputs

Includes `rescue_pseudo_boot_final_readiness.json`, all runtime manifests under `build/rescue/runtime/`, branding and zero-state handoffs.

## Version

After a green test pass, consider manual **1.8.0**; no automatic bump.
