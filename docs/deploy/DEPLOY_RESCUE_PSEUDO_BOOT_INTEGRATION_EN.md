# Deploy — Rescue pseudo-boot integration (EN)

## Purpose

Simulates a **full rescue boot initialization** as JSON artifacts under `build/rescue/` plus safety and final readiness handoffs under `docs/evidence/runtime-results/handoff/` — **no** real VM, no ISO boot, no bootloader, no `systemd` host starts, no HTTP calls (backend health is static analysis of `app.py` / `routes.py` only).

## API

| Method | Path |
|--------|------|
| `POST` | `/api/deploy/rescue/pseudo-boot/manifest` |
| `POST` | `/api/deploy/rescue/pseudo-boot/service-startup` |
| `POST` | `/api/deploy/rescue/pseudo-boot/overlay-strategy` |
| `POST` | `/api/deploy/rescue/pseudo-boot/backend-health` |
| `POST` | `/api/deploy/rescue/pseudo-boot/recovery-ui` |
| `POST` | `/api/deploy/rescue/pseudo-boot/safety-validation` |
| `POST` | `/api/deploy/rescue/pseudo-boot/final-readiness` |

Codes: `DEPLOY_RESCUE_PSEUDO_BOOT_MANIFEST_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (same pattern for `SERVICE_STARTUP`, `OVERLAY_STRATEGY`, `BACKEND_HEALTH`, `RECOVERY_UI`, `SAFETY_VALIDATION`). Final gate: `DEPLOY_RESCUE_PSEUDO_BOOT_FINAL_READINESS_READY` when `gate_status` is `ready`.

Request body: `explicit_overwrite` (bool), same as other deploy-rescue endpoints.

## Forbidden actions

No QEMU, no VirtualBox launch, no `grub-mkrescue`, no `xorriso`, no `chroot`, no `mount --bind`, no `systemctl` orchestration from this runner, no release/publish.

## Recovery UI scan

Legacy string checks are limited to `frontend/src/pages/InspectRun.tsx` (operator rescue UI) so documentation pages mentioning legacy names do not block this boot gate.

## Version

After a green test pass, consider manual **1.8.0**; no automatic bump.
