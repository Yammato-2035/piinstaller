# Release-Profil Restore — Operator-Ingest

**Ingest-Zeitpunkt:** 2026-06-02T18:03:05Z (read-only Verifikation)  
**HEAD (Workspace):** `050d119`  
**Branch:** `main`

## Bewertung

| Feld | Wert |
|------|------|
| **`release_restore_status`** | **ok** |
| **`release_restore_blocked_sudo_required`** | **resolved** |
| **`local_lab_open_after_smoke`** | **false** |

## Services

| Service | Status |
|---------|--------|
| `setuphelfer-backend.service` | **active** |
| `setuphelfer.service` | **active** |

## Gates

| Skript | Exit | Anmerkung |
|--------|------|-----------|
| `check-runtime-profile-deploy-gate.sh` | **0** | `profile_gate: OK`; legacy exit 20 informational only |
| `check-runtime-deploy-gate.sh` | **20** | Legacy non-profile-aware; Dev-Dashboard 404 erwartbar |

## Runtime (`/api/version`)

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | `disabled_by_profile` |
| `startup_diagnostics_status` | `ok` |
| `router_registry_summary` | `registered=0`, `disabled_by_profile=5`, `import_failed=0` |

## API (Port 8000)

| Endpoint | HTTP | Ergebnis |
|----------|------|----------|
| `/api/version` | **200** | Profil `release`, Gate grün |
| `/api/dev-dashboard/status` | **404** | `PROFILE_ROUTE_BLOCKED` — **expected_profile_block** |
| `/api/fleet/sessions` | **404** | `PROFILE_ROUTE_BLOCKED` — **expected_profile_block** |

## DCC-Port-Mapping (unverändert gültig)

- UI/Cockpit: http://127.0.0.1:3001/?window=cockpit
- API: http://127.0.0.1:8000/api/...
- **8080** = nginx, nicht SetupHelfer

## Fleet-Smoke (unverändert gültig)

Session `fleet-manual_fleet_heartbeat_fix_after_script_fix_20260602_164249` — Create → Heartbeat(`running`) → Finish OK. Fix `55b7bce` in `/opt`.
