# Backend Watchdog Evidence Path Fix — Result

**Datum:** 2026-06-03

## Root Cause

**`permission_denied`:** `backend_health_latest.json` unter `/opt` mit Modus **600** (Owner `gabriel`). Backend-API (`setuphelfer`) konnte die vorhandene Datei nicht lesen → `status=unknown`, `current_health=null`.

Zusätzlich: Loader ohne `searched_paths` und ohne klare Permission-Meldung.

## Fix (Workspace)

- Skript: ENV-Overrides, Pfad-JSON-Felder, **`chmod 664`**
- Loader: `/opt`-first-Suche, `searched_paths`, Permission-Hinweis

## Live

| Aussage | Wert |
|---------|------|
| Evidence unter `/opt` lesbar (664) | **yes** (nach Healthcheck) |
| API live unter local_lab | **pending** (Operator-Deploy Backend-Modul) |
| release | **unchanged** |
| QEMU | **no** |

## Operator-Abschluss

1. `sudo ./scripts/deploy-to-opt.sh`
2. `/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh`
3. local_lab → `curl /api/dev-dashboard/backend-health`
4. release restore
5. QEMU Smoke wenn API ok
