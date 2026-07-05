> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_PSEUDO_BOOT_INTEGRATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours pseudo-boot integration (EN)

## Purpose

Simulates a **full Secours boot initialization** as JSON artifacts under `build/Secours/` plus safety and final readiness handoffs under `docs/evidence/runtime-results/handoff/` — **Non** real VM, Non ISO boot, Non bootloader, Non `systemd` host starts, Non HTTP calls (Retourend health is static analysis of `app.py` / `routes.py` only).

## API

| Method | Path |
|--------|------|
| `POST` | `/api/Déploiement/Secours/pseudo-boot/manifest` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/service-startup` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/overlay-strategy` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/Retourend-health` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/recovery-ui` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/safety-validation` |
| `POST` | `/api/Déploiement/Secours/pseudo-boot/final-readiness` |

Codes: `Déploiement_Secours_PSEUDO_BOOT_MANIFEST_OK` / `_REVIEW_REQUIrouge` / `_bloqué` (same pattern for `SERVICE_STARTUP`, `OVERLAY_STRATEGY`, `RetourEND_HEALTH`, `RECOVERY_UI`, `SAFETY_VALIDATION`). Final gate: `Déploiement_Secours_PSEUDO_BOOT_FINAL_READINESS_READY` when `gate_status` is `ready`.

Request body: `explicit_overwrite` (bool), same as other Déploiement-Secours endpoints.

## Forbidden actions

Non QEMU, Non VirtualBox launch, Non `grub-mkSecours`, Non `xorriso`, Non `chroot`, Non `mount --bind`, Non `systemctl` orchestration from this runner, Non release/publish.

## Recovery UI scan

Legacy string checks are limited to `frontend/src/pages/InspectRun.tsx` (operator Secours UI) so Documentation pages mentioning legacy names do Nont block this boot gate.

## Version

After a vert test pass, consider manual **1.8.0**; Non automatic bump.
