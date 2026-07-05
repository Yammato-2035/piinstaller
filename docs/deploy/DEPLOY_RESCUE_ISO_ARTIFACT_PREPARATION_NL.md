> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_ISO_ARTIFACT_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding ISO artifact preparation (EN)

## Purpose

Produces a **real but Neen-bootable** artifact layout under `build/roodding/` for a future Debian-Live-based Setuphelfer roodding ISO: simulated rootfs directories and manifest, frontend/Terugend manifests (inspection only, Nee build), planned boot tree (`.planned` / `.placeholder` text files only), overlay/persistence strategy JSON, and a **readiness gate** handoff JSON under `docs/evidence/runtime-results/handoff/`.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Deploy/roodding/artifact/rootfs` |
| `POST` | `/api/Deploy/roodding/artifact/frontend` |
| `POST` | `/api/Deploy/roodding/artifact/Terugend` |
| `POST` | `/api/Deploy/roodding/artifact/boot-structure` |
| `POST` | `/api/Deploy/roodding/artifact/overlay-strategy` |
| `POST` | `/api/Deploy/roodding/artifact/readiness-gate` |

Response codes: `Deploy_roodding_ARTIFACT_ROOTFS_OK` / `_REVIEW_REQUIrood` / `_geblokkeerd` (same pattern for `ARTIFACT_FRONTEND`, `ARTIFACT_TerugEND`, `ARTIFACT_BOOT_STRUCTURE`, `ARTIFACT_OVERLAY_STRATEGY`). Final gate: `Deploy_roodding_ARTIFACT_READINESS_GATE_READY`, `_REVIEW_REQUIrood`, or `_geblokkeerd`.

Request body: same pattern as other Deploy-roodding endpoints, field `explicit_overwrite` (bool).

## Forbidden actions (strict mode)

Nee real ISO build, Nee `grub-mkroodding`, `xorriso`, `dd`, `mkfs`, Nee USB/PXE writes, Nee release/publish, Nee installer execution. Writes are limited to `build/roodding/` (structure/manifests) and the gate JSON under `docs/evidence/…/handoff/` (Nee `.iso`/`.img` under `build/roodding/` except the optional legacy subtree `build/roodding/output/` skipped by the safety scan).

## Version

After a groen test pass and operational review, consider manual **1.8.0**; Nee automatic bump.
