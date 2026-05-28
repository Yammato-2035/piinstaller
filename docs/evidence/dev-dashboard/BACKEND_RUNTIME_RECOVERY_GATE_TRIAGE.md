# Backend Runtime Recovery Gate — Triage

Datum: 2026-05-28

## Service-Status

- `setuphelfer-backend.service`: `active (running)`
- `setuphelfer.service`: `active (running)`
- Backend-MainPID: `138932`
- Prozess: `/opt/setuphelfer/backend/venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1`

## Port-Status

- Port `8000`: LISTEN vorhanden (`127.0.0.1:8000`)
- Port `3001`: LISTEN vorhanden
- Port `3002`: LISTEN vorhanden (node/vite)

## HTTP-Probe

- `curl http://127.0.0.1:8000/api/version` (3s/10s): Timeout
- `curl http://127.0.0.1:8000/health` (3s/10s): Timeout

## Journal-Befund

- `journalctl -u setuphelfer-backend.service`: keine Einträge sichtbar im aktuellen Nutzerkontext (`systemd-journal`/`adm`-Hinweis)
- Daher keine belastbare Import-/Permission-Root-Cause direkt aus Journal ableitbar.

## Klassifikation

- `backend_unknown_failure`
- Zusatzsignale:
  - Service läuft, aber API antwortet nicht
  - Port 8000 lauscht, jedoch HTTP unresponsive
  - Journalzugriff eingeschränkt

## Restart-Policy

- **Kein Restart ausgeführt** (keine Freigabe `BACKEND_RESTART_FREIGEGEBEN`).
- Nächster Schritt: Operator-Freigabe einholen und gezielten Service-Restart + Gate-Recheck durchführen.
