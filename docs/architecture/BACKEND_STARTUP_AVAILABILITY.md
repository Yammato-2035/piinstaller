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
- `/health` muss leichtgewichtig sein (keine Dateiscans, keine Roadmap-/Drift-Berechnung).
- `/api/version` muss robust und schnell sein, unabhaengig von optionalen Dashboard-/Evidence-Dateien.
- `backend_hanging` blockiert Runtime-Gate und Runtime-nahe Operationen hart.
