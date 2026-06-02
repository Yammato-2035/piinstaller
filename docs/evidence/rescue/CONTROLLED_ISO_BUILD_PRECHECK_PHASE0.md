# Controlled ISO Build Precheck — Phase 0

**Stand:** 2026-06-02  
**HEAD:** `4df53eb`  
**Branch:** `main`

## Runtime

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | **disabled_by_profile** |

## Gates

| Skript | Exit |
|--------|------|
| `check-runtime-profile-deploy-gate.sh` | **0** |
| `check-runtime-deploy-gate.sh` | **20** (legacy, erwartbar unter `release`) |

## Route-Blocks (release, erwartbar)

| Route | Code |
|-------|------|
| `/api/dev-dashboard/status` | `PROFILE_ROUTE_BLOCKED` |
| `/api/fleet/sessions` | `PROFILE_ROUTE_BLOCKED` |
| `/api/rescue-agent/sessions` | `PROFILE_ROUTE_BLOCKED` |

## Bewertung

**`release_baseline_ok=yes`**

Services: `setuphelfer-backend`, `setuphelfer` **active**.
