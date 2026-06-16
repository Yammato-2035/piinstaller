# R.7 — Phase 0 Status

**Datum:** 2026-06-10  
**Kampagne:** `CAMPAIGN_R7_HARDWARE_BOOT_PERSISTENCE_VALIDATION`

## Git

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `57e30d9` |
| R.6-Änderungen committed | **nein** (Workspace-Drift, siehe `R7_R6_VALIDATION.md`) |

`git status --short`: viele modifizierte/untracked Dateien inkl. R.6-Artefakte (`setuphelfer-rescue-boot-evidence-init`, `test_rescue_boot_persistence_hook_r6.py`, R6-Docs).

## Version

| Quelle | `project_version` |
|--------|-------------------|
| `config/version.json` (Workspace) | **1.7.17.0** |
| `GET /api/version` (Runtime `/opt`) | **1.7.13.2** |

**Drift:** Workspace ≠ Runtime API.

## Runtime-Gate

| Gate | Exit | Befund |
|------|------|--------|
| `./scripts/check-runtime-deploy-gate.sh` | **20** | `LEGACY_GATE_NON_PROFILE_AWARE` — `/api/dev-dashboard/status` HTTP 404 (Profil release, erwartet) |
| `./scripts/check-backend-version-gate.sh` | **14** | Drift `workspace=1.7.17.0` vs `api=1.7.13.2` |
| `setuphelfer-backend.service` | — | API `/api/version` HTTP 200 |
| `backend_runtime_path` | `/opt/setuphelfer/backend` | bestätigt |

## R.7-Relevanz

R.7 betrifft **Rescue-Stick/ISO**, nicht `/opt`-Deploy. Runtime-Gate-Drift ist dokumentiert, blockiert aber **keinen** Workspace-only-Validierungsschritt.

## Entscheidung Phase 0

**Weiter** mit Phasen 1–9 (Nachweis/Bewertung). Phasen 2/4/5 erfordern Operator.
