# Backend Startup Availability (KB)

## Problem

Ein laufender Service und ein offener Port koennen trotzdem in einen Hang-Zustand fuehren: HTTP-Endpunkte antworten nicht, Control Center wirkt leer oder unvollstaendig.

## Harte Kriterien

- `backend_hanging` ist ein eigener Fehlerzustand.
- `/health` muss schnell (<500ms typisch) und leichtgewichtig bleiben.
- `/api/version` darf keine schweren Dashboard-Abhaengigkeiten haben.
- Runtime-Gate muss Timeout/Hang explizit melden.

## Operator-Hinweis

Bei `backend_hanging`:

1. `sudo systemctl status setuphelfer-backend.service --no-pager`
2. `sudo journalctl -u setuphelfer-backend.service -n 200 --no-pager`
3. `sudo systemctl restart setuphelfer-backend.service`
4. `curl -sS -m 5 http://127.0.0.1:8000/health`
5. `curl -sS -m 5 http://127.0.0.1:8000/api/version`
6. `./scripts/check-runtime-deploy-gate.sh` (Exit 17/18 = Hang; 14 = deploy_drift)

## Watchdog-MVP (nicht aktiv)

- `scripts/healthcheck/setuphelfer-backend-healthcheck.sh`
- systemd `.example` unter `packaging/systemd/`
- `ENABLE_RESTART=0` Standard
