# DCC-Smoke nach Deploy 2e602d0

**Stand:** 2026-06-02  
**Status:** **blocked** (Deploy nicht erfolgt; Profil `release`)

## Begründung

| Blocker | Detail |
|---------|--------|
| Deploy | `deploy_blocked_sudo_required` — Runtime noch alter Stand |
| Profil | `GET /api/dev-dashboard/status` → **404 `PROFILE_ROUTE_BLOCKED`** in `release` (**erwartbar**) |

Ohne Deploy und ohne `local_lab`-Drop-in ist kein DCC-Funktionssmoke möglich.

## Erwartetes Verhalten (nach Deploy + optional local_lab)

| Zustand | Erwartung |
|---------|-----------|
| `release` | DCC API blockiert; UI darf nicht crashen |
| `local_lab` | `/api/dev-dashboard/status` 200; RescueAgentPanel leer/Stub OK |

## local_lab

Nicht aktiviert in diesem Lauf (Deploy-Voraussetzung fehlt).

## UI (unverändert)

Frontend zuletzt **54 Vitest passed** am Commit `2e602d0` (Workspace-venv, vor Deploy-Lauf).
