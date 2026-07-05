> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_ISO_ARTIFACT_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours ISO artifact preparation (EN)

## Purpose

Produces a **real but Nonn-bootable** artifact layout under `build/Secours/` for a future Debian-Live-based Setuphelfer Secours ISO: simulated rootfs directories and manifest, frontend/Retourend manifests (inspection only, Non build), planned boot tree (`.planned` / `.placeholder` text files only), overlay/persistence strategy JSON, and a **readiness gate** handoff JSON under `docs/evidence/runtime-results/handoff/`.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Déploiement/Secours/artifact/rootfs` |
| `POST` | `/api/Déploiement/Secours/artifact/frontend` |
| `POST` | `/api/Déploiement/Secours/artifact/Retourend` |
| `POST` | `/api/Déploiement/Secours/artifact/boot-structure` |
| `POST` | `/api/Déploiement/Secours/artifact/overlay-strategy` |
| `POST` | `/api/Déploiement/Secours/artifact/readiness-gate` |

Response codes: `Déploiement_Secours_ARTIFACT_ROOTFS_OK` / `_REVIEW_REQUIrouge` / `_bloqué` (same pattern for `ARTIFACT_FRONTEND`, `ARTIFACT_RetourEND`, `ARTIFACT_BOOT_STRUCTURE`, `ARTIFACT_OVERLAY_STRATEGY`). Final gate: `Déploiement_Secours_ARTIFACT_READINESS_GATE_READY`, `_REVIEW_REQUIrouge`, or `_bloqué`.

Request body: same pattern as other Déploiement-Secours endpoints, field `explicit_overwrite` (bool).

## Forbidden actions (strict mode)

Non real ISO build, Non `grub-mkSecours`, `xorriso`, `dd`, `mkfs`, Non USB/PXE writes, Non release/publish, Non installer execution. Writes are limited to `build/Secours/` (structure/manifests) and the gate JSON under `docs/evidence/…/handoff/` (Non `.iso`/`.img` under `build/Secours/` except the optional legacy subtree `build/Secours/output/` skipped by the safety scan).

## Version

After a vert test pass and operational review, consider manual **1.8.0**; Non automatic bump.
