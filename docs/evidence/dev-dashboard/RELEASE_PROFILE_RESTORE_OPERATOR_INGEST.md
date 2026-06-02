# Release-Profil Restore — Operator-Ingest

**Ingest-Zeitpunkt:** 2026-06-02 (UTC, nach Operator-Restore)  
**HEAD (Workspace):** `9438901`  
**Branch:** `main`

## Services

| Service | Status |
|---------|--------|
| `setuphelfer-backend.service` | **active** |
| `setuphelfer.service` | **active** |

## Gates

| Skript | Exit | Anmerkung |
|--------|------|-----------|
| `check-runtime-profile-deploy-gate.sh` | **0** | Profil-Gate grün |
| `check-runtime-deploy-gate.sh` | **20** | Legacy, erwartbar unter `release` (Dev-Dashboard 404) |

## Runtime (`/api/version`)

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | `disabled_by_profile` |
| `startup_diagnostics_status` | `ok` |

## API (Port 8000)

| Endpoint | HTTP | Code / Anmerkung |
|----------|------|------------------|
| `/api/version` | **200** | Profil `release` |
| `/api/dev-dashboard/status` | **404** | `PROFILE_ROUTE_BLOCKED` — erwartbar |
| `/api/fleet/sessions` | **404** | `PROFILE_ROUTE_BLOCKED` — erwartbar |

## Vorheriger Blocker

`release_restore_blocked_sudo_required` — durch Operator-Restore aufgehoben.

## Fleet / DCC (unverändert gültig)

- Fleet-Smoke **grün** (Session `…164249`, Fix `55b7bce` in `/opt`)
- DCC-Port-Mapping **grün** (3001 UI, 8000 API, 8080 nginx)
