# Runtime Ports — Profile Gating Live Check

**Datum:** 2026-06-03  
**Profil:** `release`

## Ergebnisse

| Route | HTTP | Code | Blockiert |
|-------|------|------|-----------|
| `/api/dev-dashboard/backend-health` | 404 | `PROFILE_ROUTE_BLOCKED` | **yes** |
| `/api/fleet/sessions` | 404 | `PROFILE_ROUTE_BLOCKED` | **yes** |
| `/api/rescue-agent/sessions` | 404 | `PROFILE_ROUTE_BLOCKED` | **yes** |

Artefakte:

- `runtime_ports_backend_health_release_block_latest.txt`
- `runtime_ports_fleet_release_block_latest.txt`
- `runtime_ports_rescue_agent_release_block_latest.txt`

## Bewertung

| Frage | Antwort |
|-------|---------|
| backend-health unter release blockiert | **yes** |
| fleet unter release blockiert | **yes** |
| rescue-agent unter release blockiert | **yes** |
| kein Gating-Bug | **yes** |

## Status

**ok**

Dev-Routen sind unter `release` erwartungsgemäß gesperrt; kein offener Gating-Bug.
