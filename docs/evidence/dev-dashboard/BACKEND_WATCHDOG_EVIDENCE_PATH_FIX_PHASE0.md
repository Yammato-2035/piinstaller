# Backend Watchdog Evidence Path Fix — Phase 0

**Datum:** 2026-06-03  
**HEAD:** `4fbf423` (vor Fix-Commit)  
**Branch:** `main`

| Prüfpunkt | Wert |
|-----------|------|
| Runtime-Profil | **release** |
| profile_gate_status | **green** |
| Backend erreichbar | **yes** |
| API-Fehler (vor Fix) | `backend_health_latest.json not found`, `current_health=null`, `stale=true` |
| Kein ISO/QEMU/USB/Backup/Restore | **yes** |

**Hinweis:** Unter release ist die Route `PROFILE_ROUTE_BLOCKED`; der Fehler trat unter **local_lab** nach Deploy auf.
