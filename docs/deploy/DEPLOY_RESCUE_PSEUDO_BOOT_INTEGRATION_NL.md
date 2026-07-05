> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_PSEUDO_BOOT_INTEGRATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding pseudo-boot integration (EN)

## Purpose

Simulates a **full roodding boot initialization** as JSON artifacts under `build/roodding/` plus safety and final readiness handoffs under `docs/evidence/runtime-results/handoff/` — **Nee** real VM, Nee ISO boot, Nee bootloader, Nee `systemd` host starts, Nee HTTP calls (Terugend health is static analysis of `app.py` / `routes.py` only).

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Deploy/roodding/pseudo-boot/manifest` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/service-startup` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/overlay-strategy` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/Terugend-health` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/recovery-ui` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/safety-validation` |
| `POST` | `/api/Deploy/roodding/pseudo-boot/final-readiness` |

Codes: `Deploy_roodding_PSEUDO_BOOT_MANIFEST_OK` / `_REVIEW_REQUIrood` / `_geblokkeerd` (same pattern for `SERVICE_STARTUP`, `OVERLAY_STRATEGY`, `TerugEND_HEALTH`, `RECOVERY_UI`, `SAFETY_VALIDATION`). Final gate: `Deploy_roodding_PSEUDO_BOOT_FINAL_READINESS_READY` when `gate_status` is `ready`.

Request body: `explicit_overwrite` (bool), same as other Deploy-roodding endpoints.

## Forbidden actions

Nee QEMU, Nee VirtualBox launch, Nee `grub-mkroodding`, Nee `xorriso`, Nee `chroot`, Nee `mount --bind`, Nee `systemctl` orchestration from this runner, Nee release/publish.

## Recovery UI scan

Legacy string checks are limited to `frontend/src/pages/InspectRun.tsx` (operator roodding UI) so Documentatie pages mentioning legacy names do Neet block this boot gate.

## Version

After a groen test pass, consider manual **1.8.0**; Nee automatic bump.
