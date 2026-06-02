# Deploy-Sync 2e602d0 — Post-Deploy Ergebnis

**Stand:** 2026-06-02  
**Status:** **ok** (Deploy + Restart durch Operator; Profil `release`)

## Deploy / Restart

| Aktion | Ergebnis |
|--------|----------|
| `deploy-to-opt.sh` (Worktree `2e602d0`) | **OK** (Operator-Terminal) |
| `systemctl restart setuphelfer-backend.service` | **OK** |
| `setuphelfer-backend.service` | **active** |

## `/opt` Verifikation

| Pfad | Ergebnis |
|------|----------|
| `/opt/setuphelfer/backend/rescue_agent/routers.py` | **vorhanden** |
| `/opt/setuphelfer/backend/app_bootstrap/app_factory.py` | **vorhanden** |

## HTTP (release)

| Endpoint | HTTP | Anmerkung |
|----------|------|-----------|
| `/api/version` | **200** | Diagnosefelder live |
| `/openapi.json` | **200** | |
| `/api/dev-dashboard/status` | **404** | `PROFILE_ROUTE_BLOCKED` — **erwartbar** |
| `/api/fleet/sessions` | **404** | `PROFILE_ROUTE_BLOCKED` — **erwartbar** |

## `/api/version` (Live)

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `profile_gate_status` | `green` |
| `rescue_agent_router_status` | `disabled_by_profile` |
| `rescue_agent_router_error` | *(leer)* |
| `startup_diagnostics_status` | `ok` |
| `router_registry_summary` | `registered:0`, `disabled_by_profile:5`, `import_failed:0` |

## Runtime-Gates

| Gate | Exit | Anmerkung |
|------|------|-----------|
| `check-runtime-deploy-gate.sh` | **20** | legacy: dev-dashboard 404 in release — dokumentiert |
| `check-runtime-profile-deploy-gate.sh` | **0** | **OK** |

## Offen

- **Fleet-Live-Smoke** und **DCC-Funktionssmoke** erfordern `local_lab` (Operator Drop-in + Restart).
- Worktree unter `/tmp` erhält kein Backend-Workspace-Drop-in (Deploy-Warnung erwartbar).
