# Backend Watchdog Evidence Path Fix — API Live Smoke

**Datum:** 2026-06-03

**Nicht ausgeführt** in Agent-Session:

1. Deploy des aktualisierten `dev_dashboard_backend_health.py` nach `/opt` (sudo blockiert).
2. local_lab-Profilwechsel (sudo).

## Erwartung nach Operator-Abschluss

| Prüfpunkt | Erwartung |
|-----------|-----------|
| HTTP | **200** |
| `source_path` | `/opt/setuphelfer/docs/evidence/dev-dashboard/backend_health_latest.json` |
| `searched_paths` | enthält `/opt`-Pfad mit `state=ok` |
| `stale` | **false** (frischer Healthcheck) |
| `current_health.overall_status` | **ok** |

| **Status** | **blocked** |
