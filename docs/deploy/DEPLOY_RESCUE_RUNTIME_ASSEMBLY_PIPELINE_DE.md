# Deploy — Rescue Runtime Assembly Pipeline (DE)

## Zweck

Erzeugt eine **vollständige zusammengesetzte Rescue-Runtime-Struktur** unter `build/rescue/runtime/` (Verzeichnisse, Platzhalter, JSON-Manifeste, Template-Shellskripte) **ohne** ISO-Build, ohne VM, ohne echten Dienststart.

## API

| Methode | Pfad |
|---------|------|
| `POST` | `/api/deploy/rescue/runtime/root` |
| `POST` | `/api/deploy/rescue/runtime/backend` |
| `POST` | `/api/deploy/rescue/runtime/frontend` |
| `POST` | `/api/deploy/rescue/runtime/recovery` |
| `POST` | `/api/deploy/rescue/runtime/offline-config` |
| `POST` | `/api/deploy/rescue/runtime/startup-scripts` |
| `POST` | `/api/deploy/rescue/runtime/final-gate` |
| `POST` | `/api/deploy/rescue/runtime/safety-validation` |

Codes: `DEPLOY_RESCUE_RUNTIME_ROOT_OK` / `_REVIEW_REQUIRED` / `_BLOCKED` (analog für `RUNTIME_BACKEND`, `RUNTIME_FRONTEND`, `RUNTIME_RECOVERY`, `RUNTIME_OFFLINE_CONFIG`, `RUNTIME_STARTUP_SCRIPTS`, `RUNTIME_SAFETY_VALIDATION`). Final-Gate: `DEPLOY_RESCUE_RUNTIME_FINAL_GATE_READY` bei `gate_status: ready`.

## Verbote

Kein `qemu`, kein `grub-mkrescue`, kein `xorriso`, kein `dd`, kein `mkfs`, kein `chroot`, kein `mount --bind`, kein echter Restore, kein `systemctl` durch diese Pipeline.

## Final-Gate-Inputs

Unter anderem `rescue_pseudo_boot_final_readiness.json`, alle Runtime-Manifeste unter `build/rescue/runtime/`, Branding- und Zero-State-Handoffs.

## Version

Nach grüner Testkette manuell **1.8.0** erwägen; kein automatischer Bump.
