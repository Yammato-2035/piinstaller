# DCC-Smoke nach Deploy 2e602d0

**Stand:** 2026-06-02  
**Status:** **blocked_by_profile_expected** (Deploy OK; Profil `release`)

## Begründung

| Prüfung | Ergebnis |
|---------|----------|
| Deploy nach `/opt` | **OK** (`2e602d0` Worktree) |
| `GET /api/dev-dashboard/status` | **404 `PROFILE_ROUTE_BLOCKED`** in `release` — **erwartbar** |
| `local_lab` | **nicht** aktiviert (Agent-Shell ohne sudo) |

Funktionssmoke (Dashboard-API 200) erfordert `local_lab`-Drop-in.

## Erwartetes Verhalten (nach Deploy + optional local_lab)

| Zustand | Erwartung |
|---------|-----------|
| `release` | DCC API blockiert; UI darf nicht crashen |
| `local_lab` | `/api/dev-dashboard/status` 200; RescueAgentPanel leer/Stub OK |

## local_lab

Nicht aktiviert in diesem Lauf (Deploy-Voraussetzung fehlt).

## UI (unverändert)

Frontend zuletzt **54 Vitest passed** am Commit `2e602d0` (Workspace-venv, vor Deploy-Lauf).
