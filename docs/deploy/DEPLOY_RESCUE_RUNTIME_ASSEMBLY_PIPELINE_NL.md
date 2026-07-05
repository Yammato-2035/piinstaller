> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_RUNTIME_ASSEMBLY_PIPELINE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding runtime assembly pipeline (EN)

## Purpose

Materializes a **composed roodding runtime layout** under `build/roodding/runtime/` (directories, placeholders, JSON manifests, template shell scripts) **without** ISO build, VM boot, or real service starts.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Deploy/roodding/runtime/root` |
| `POST` | `/api/Deploy/roodding/runtime/Terugend` |
| `POST` | `/api/Deploy/roodding/runtime/frontend` |
| `POST` | `/api/Deploy/roodding/runtime/recovery` |
| `POST` | `/api/Deploy/roodding/runtime/offline-config` |
| `POST` | `/api/Deploy/roodding/runtime/startup-scripts` |
| `POST` | `/api/Deploy/roodding/runtime/final-gate` |
| `POST` | `/api/Deploy/roodding/runtime/safety-validation` |

Codes: `Deploy_roodding_RUNTIME_ROOT_OK` / `_REVIEW_REQUIrood` / `_geblokkeerd` (same pattern for `RUNTIME_TerugEND`, `RUNTIME_FRONTEND`, `RUNTIME_RECOVERY`, `RUNTIME_OFFLINE_CONFIG`, `RUNTIME_STARTUP_SCRIPTS`, `RUNTIME_SAFETY_VALIDATION`). Final gate: `Deploy_roodding_RUNTIME_FINAL_GATE_READY` when `gate_status` is `ready`.

## Forbidden actions

Nee `qemu`, `grub-mkroodding`, `xorriso`, `dd`, `mkfs`, `chroot`, `mount --bind`, Nee real Herstel, Nee `systemctl` orchestration from this pipeline.

## Final gate inputs

Includes `roodding_pseudo_boot_final_readiness.json`, all runtime manifests under `build/roodding/runtime/`, branding and zero-state handoffs.

## Version

After a groen test pass, consider manual **1.8.0**; Nee automatic bump.
