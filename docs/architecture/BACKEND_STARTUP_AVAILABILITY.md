# BACKEND_STARTUP_AVAILABILITY

## Ziel

Backend-Verfuegbarkeit ist eine harte Voraussetzung fuer Runtime-Gate, Developer Control Center, Rescue, Backup und Restore.

## Zustandsmodell

1. `backend_ok`
   - Service aktiv
   - Port 8000 offen
   - `/health` HTTP 200
   - `/api/version` HTTP 200

2. `backend_down`
   - Service inactive/failed oder Port nicht offen

3. `backend_hanging` (**harter Fehler**)
   - Service aktiv
   - Port 8000 LISTEN
   - `/health` oder `/api/version` timeout

4. `backend_degraded`
   - `/health` OK
   - `/api/version` oder Dashboard-API fehlerhaft

5. `backend_unknown`
   - Zustand nicht eindeutig messbar

## Architektur-Regeln

- Port offen reicht **nicht** als Lebenszeichen.
- `systemd active` reicht **nicht** als Lebenszeichen.
- `/health` und `/api/version` laufen ueber `backend/core/liveness.py` (kein Dashboard-Import).
- Dev-Dashboard schwere Abschnitte (`deploy_drift`, `cockpit_enrich`) mit Thread-Timeout isoliert.
- Runtime-Gate: Exit **17** (Health-Timeout), **18** (Version-Timeout bei Health OK).
- `backend_hanging` blockiert Runtime-Gate und Runtime-nahe Operationen hart.

Siehe auch `BACKEND_WATCHDOG_MVP_DECISION.md`.
