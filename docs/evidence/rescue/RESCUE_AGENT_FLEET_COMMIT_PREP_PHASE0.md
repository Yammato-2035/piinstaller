# Rescue Agent / Fleet — Commit-Prep Phase 0

**Stand:** 2026-06-02  
**Vorgänger-Commit:** `00615d5` (App-Bootstrap)

## Git

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD (Start) | `00615d5` |
| Ziel | separater Rescue-Agent/Fleet-Commit |

## Runtime (readonly)

| Feld | Wert |
|------|------|
| `setuphelfer-backend.service` | active |
| Profil (live API) | `release` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| Legacy Runtime-Gate | non-zero (dev-dashboard 404 in release — erwartbar) |
| Profil-Gate | OK (`check-runtime-profile-deploy-gate.sh`) |
| Deploy-Drift | **ja** — `rescue_agent/`, Fleet-Heartbeat, `install_profile` nicht in `/opt` |

## HTTP (readonly)

| Endpoint | Ergebnis |
|----------|----------|
| `/api/version` | 200 |
| `/openapi.json` | 200 |
| `/api/dev-dashboard/status` | 404 `PROFILE_ROUTE_BLOCKED` |
| `/api/rescue-agent/sessions` (live) | nicht abgenommen (Drift) |

## Erlaubt / verboten

- Workspace-Import, py_compile, pytest, Frontend build/test: **ja**
- Live Fleet-Smoke, Rescue-Ingest, Deploy, Restart, Profilwechsel: **nein**

## Uncommitted (Überblick)

- **~33 modified**, **~119 untracked** (siehe `RESCUE_AGENT_FLEET_UNCOMMITTED_CLASSIFICATION.md`)
- Commitfähig: `backend/rescue_agent/`, Fleet-Heartbeat, Tests, Frontend-Panels, Rescue-Doku
- Ausgeschlossen: `build/**`, QEMU-Evidence, `.cursor/rules`, ISO-Artefakte, `__pycache__`
