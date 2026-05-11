# Deploy — Rescue Pseudo-Boot-Integration (DE)

## Zweck

Simuliert eine **vollständige Rescue-Boot-Initialisierung** als JSON-Artefakte unter `build/rescue/` plus Safety- und Final-Readiness-Handoffs unter `docs/evidence/runtime-results/handoff/` — **ohne** echte VM, ohne ISO-Boot, ohne Bootloader, ohne `systemd`-Start am Host, ohne HTTP-Probes (Backend-Health nur statische Analyse von `app.py` / `routes.py`).

## API

| Methode | Pfad |
|---------|------|
| `POST` | `/api/deploy/rescue/pseudo-boot/manifest` |
| `POST` | `/api/deploy/rescue/pseudo-boot/service-startup` |
| `POST` | `/api/deploy/rescue/pseudo-boot/overlay-strategy` |
| `POST` | `/api/deploy/rescue/pseudo-boot/backend-health` |
| `POST` | `/api/deploy/rescue/pseudo-boot/recovery-ui` |
| `POST` | `/api/deploy/rescue/pseudo-boot/safety-validation` |
| `POST` | `/api/deploy/rescue/pseudo-boot/final-readiness` |

Codes: `DEPLOY_RESCUE_PSEUDO_BOOT_MANIFEST_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (analog für `SERVICE_STARTUP`, `OVERLAY_STRATEGY`, `BACKEND_HEALTH`, `RECOVERY_UI`, `SAFETY_VALIDATION`). Final: `DEPLOY_RESCUE_PSEUDO_BOOT_FINAL_READINESS_READY` bei `gate_status: ready`.

Body: `explicit_overwrite` (bool) wie bei anderen Deploy-Rescue-Endpunkten.

## Verbote

Kein QEMU, kein VirtualBox-Start, kein `grub-mkrescue`, kein `xorriso`, kein `chroot`, kein `mount --bind`, kein `systemctl` zur Laufzeitsteuerung durch diesen Runner, kein Release/Publish.

## Recovery-UI-Scan

Legacy-String-Prüfung nur auf `frontend/src/pages/InspectRun.tsx` (Operator-Rescue-UI); keine Vollrepo-TSX-Fläche, um dokumentierte Legacy-Hinweise in der Doku nicht mit Boot-Gates zu vermischen.

## Version

Nach grüner Testkette manuell **1.8.0** erwägen; kein automatischer Bump.
