# Deploy — Rescue ISO artifact preparation (EN)

## Purpose

Produces a **real but non-bootable** artifact layout under `build/rescue/` for a future Debian-Live-based Setuphelfer rescue ISO: simulated rootfs directories and manifest, frontend/backend manifests (inspection only, no build), planned boot tree (`.planned` / `.placeholder` text files only), overlay/persistence strategy JSON, and a **readiness gate** handoff JSON under `docs/evidence/runtime-results/handoff/`.

## API

| Method | Path |
|--------|------|
| `POST` | `/api/deploy/rescue/artifact/rootfs` |
| `POST` | `/api/deploy/rescue/artifact/frontend` |
| `POST` | `/api/deploy/rescue/artifact/backend` |
| `POST` | `/api/deploy/rescue/artifact/boot-structure` |
| `POST` | `/api/deploy/rescue/artifact/overlay-strategy` |
| `POST` | `/api/deploy/rescue/artifact/readiness-gate` |

Response codes: `DEPLOY_RESCUE_ARTIFACT_ROOTFS_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (same pattern for `ARTIFACT_FRONTEND`, `ARTIFACT_BACKEND`, `ARTIFACT_BOOT_STRUCTURE`, `ARTIFACT_OVERLAY_STRATEGY`). Final gate: `DEPLOY_RESCUE_ARTIFACT_READINESS_GATE_READY`, `_REVIEW_REQUIRED`, or `_BLOCKED`.

Request body: same pattern as other deploy-rescue endpoints, field `explicit_overwrite` (bool).

## Forbidden actions (strict mode)

No real ISO build, no `grub-mkrescue`, `xorriso`, `dd`, `mkfs`, no USB/PXE writes, no release/publish, no installer execution. Writes are limited to `build/rescue/` (structure/manifests) and the gate JSON under `docs/evidence/…/handoff/` (no `.iso`/`.img` under `build/rescue/` except the optional legacy subtree `build/rescue/output/` skipped by the safety scan).

## Version

After a green test pass and operational review, consider manual **1.8.0**; no automatic bump.
