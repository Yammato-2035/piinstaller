# Initial Public/Private and MSI Status

**Erstellt:** 2026-06-16  
**Lauf:** Commercial Boundary + MSI Windows→Linux Plan (kein Runtime/Hardware)

## Git

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `94c91f1` |
| Remote | `origin` → `https://github.com/Yammato-2035/piinstaller.git` |
| Dirty Tree | Nur untracked Evidence/Build-Artefakte; `ckb-next` Submodule modified; kein staged private Code |

## Repository-Sichtbarkeit

| Quelle | Ergebnis |
|--------|----------|
| `gh repo view` | **PUBLIC** (`Yammato-2035/piinstaller`) |

**Arbeitsmodus:** `public_repo_context`  
**Entscheidung:** `private_code_allowed: false`  
**Entscheidung:** `commercial_code_allowed_in_this_repo: false`  
**Entscheidung:** `msi_runtime_actions_allowed: false`

## Gates (read-only, vor Änderungen)

| Gate | Status | Anmerkung |
|------|--------|-----------|
| `check-runtime-deploy-gate.sh` | Legacy-Hinweis | Dev-Dashboard 404 im Profil `release` erwartet |
| `check-backend-version-gate.sh` | OK | Workspace/API `1.8.12.0` konsistent |
| `check-module-boundaries.sh` | `review_required` | 110 Warnungen (app.py Größe, Facade-Tokens) |
| `check-public-private-boundary.sh` | OK (Exit 0) | Keine privaten Pfade im Tree |

## Sensible Dateinamen (ohne Inhalt)

Gefunden per `find` (maxdepth 6), Auszug:

- `./.env` (untracked — **nicht committen**)
- `./backend/tests/test_security_sudo_store_has_password_guard_v1.py` (Test, public-safe)
- `./docs/review/security/modules/sudo-password.md` (Doku)
- `./build/rescue/.chroot-stale-*/…` (Build-Chroot, nicht committen)
- Keine committed `*.pem` / `*.key` im Workspace-Root

## Runtime (Referenz, kein Deploy in diesem Lauf)

- `/api/version` → `1.8.12.0` (nach letztem Deploy)
- `setuphelfer-backend.service` → active (Referenzstand)

## MSI / Hardware

- **Kein** MSI-Zugriff in diesem Lauf
- **Kein** Backup, Restore, Verify Deep, dd, mount, wipe
- Nur Planung, Runbooks, Contracts, Evidence-Schema
