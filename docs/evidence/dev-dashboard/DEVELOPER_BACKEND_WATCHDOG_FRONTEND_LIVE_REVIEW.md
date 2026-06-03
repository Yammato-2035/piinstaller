# Developer Backend Watchdog — Frontend Live Review

**Datum:** 2026-06-03

| Prüfpunkt | Wert |
|-----------|------|
| Port 3001 erreichbar | **yes** (Service active) |
| `/opt` Frontend dist Watchdog-Strings | **no** |
| Workspace `frontend/dist` nach build | **yes** (`backend-health`, `failure_classification`) |
| BackendHealthPanel im **live** Bundle | **no** (Deploy ausstehend) |
| DCC URL | `http://127.0.0.1:3001/?window=cockpit` |
| Manuelle Browserprüfung empfohlen | **yes** (nach Deploy + local_lab) |
| **Status** | **blocked** |

Hinweis: `/opt/.../index-DmK5vS9q.js` (2026-06-03 08:31) ohne Watchdog-Strings; Workspace-Build `index-B_ziKWju.js` enthält Watchdog.
