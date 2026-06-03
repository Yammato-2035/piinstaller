# Backend Watchdog Path Fix — Live Ingest Result

**Datum:** 2026-06-03  
**HEAD:** `fad5746`

## Zusammenfassung

| Aussage | Wert |
|---------|------|
| Watchdog-Pfadfix live | **yes** |
| Permission/Lesbarkeit behoben | **yes** (664, `/opt` source_path) |
| `/opt` Healthcheck | Exit **0**, `overall_status=ok` |
| local_lab API | **HTTP 200**, `current_health` ok, `stale=false` |
| Release-Gating | **ok** (kein Bug; TestClient **404 PROFILE_ROUTE_BLOCKED**) |
| Release restore | **ausstehend** (Runtime noch local_lab) |
| QEMU | **no** |
| Ingest JSON status | **review_required** (release restore pending) |

## QEMU-Freigabe

Erst nach Operator **release restore** und erneutem Kurzcheck `backend-health` → 404 unter release:  
**QEMU Guest Agent Smoke Operator Run**.

## Evidence

- `backend_watchdog_path_fix_live_ingest_latest.json`
- `BACKEND_WATCHDOG_PATH_FIX_OPT_HEALTHCHECK_REVIEW.md`
- `BACKEND_WATCHDOG_PATH_FIX_RELEASE_GATING_REVIEW.md`
- `BACKEND_WATCHDOG_PATH_FIX_LOCAL_LAB_API_SMOKE.md`
- Operator-Transkript: Terminal 6 (Deploy + local_lab API 200)
