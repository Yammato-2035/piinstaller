> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_RUNTIME_ASSEMBLY_PIPELINE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours runtime assembly pipeline (EN)

## Purpose

Materializes a **composed Secours runtime layout** under `build/Secours/runtime/` (directories, placeholders, JSON manifests, template shell scripts) **without** ISO build, VM boot, or real service starts.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Déploiement/Secours/runtime/root` |
| `POST` | `/api/Déploiement/Secours/runtime/Retourend` |
| `POST` | `/api/Déploiement/Secours/runtime/frontend` |
| `POST` | `/api/Déploiement/Secours/runtime/recovery` |
| `POST` | `/api/Déploiement/Secours/runtime/offline-config` |
| `POST` | `/api/Déploiement/Secours/runtime/startup-scripts` |
| `POST` | `/api/Déploiement/Secours/runtime/final-gate` |
| `POST` | `/api/Déploiement/Secours/runtime/safety-validation` |

Codes: `Déploiement_Secours_RUNTIME_ROOT_OK` / `_REVIEW_REQUIrouge` / `_bloqué` (same pattern for `RUNTIME_RetourEND`, `RUNTIME_FRONTEND`, `RUNTIME_RECOVERY`, `RUNTIME_OFFLINE_CONFIG`, `RUNTIME_STARTUP_SCRIPTS`, `RUNTIME_SAFETY_VALIDATION`). Final gate: `Déploiement_Secours_RUNTIME_FINAL_GATE_READY` when `gate_status` is `ready`.

## Forbidden actions

Non `qemu`, `grub-mkSecours`, `xorriso`, `dd`, `mkfs`, `chroot`, `mount --bind`, Non real Restauration, Non `systemctl` orchestration from this pipeline.

## Final gate inputs

Includes `Secours_pseudo_boot_final_readiness.json`, all runtime manifests under `build/Secours/runtime/`, branding and zero-state handoffs.

## Version

After a vert test pass, consider manual **1.8.0**; Non automatic bump.
