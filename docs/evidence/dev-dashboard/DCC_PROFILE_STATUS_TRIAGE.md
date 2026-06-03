# DCC Profile Status Triage

**Datum:** 2026-06-03  
**Runtime-Profil:** `release`  
**Klassifikation:** `dcc_not_available_expected_release_profile`

## Live-Checks

| Route | HTTP | Code |
|-------|------|------|
| `/api/dev-dashboard/status` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `/api/dev-dashboard/backend-health` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `/api/fleet/sessions` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `/api/version` | 200 | ok |
| Frontend `127.0.0.1:3001` | 200 | SimpleHTTP UI erreichbar |
| nginx `127.0.0.1:8080` | 200 | **nicht** DCC |

## Bewertung

**Kein DCC-Bug.** Unter `release` ist Development Control absichtlich deaktiviert. Meldung „Development Control nicht verfügbar“ / `profile=release` ist **korrekt**.

**Nicht** als Portfehler klassifizieren — Ports 8000/3001 lauschen; Blockade ist profilbedingt.

Wenn DCC aktiv benötigt wird: separater Operator-`local_lab`-Smoke (nicht Teil dieses Ingest-Laufs).

## Artefakte

- `dcc_profile_status_response_latest.txt`
- `dcc_profile_backend_health_response_latest.txt`
- `dcc_profile_fleet_response_latest.txt`
