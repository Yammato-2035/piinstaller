# Rescue-Agent Ingest Stub Smoke — Phase 0

**Stand:** 2026-06-02T18:07:55Z  
**HEAD:** `7f0704c`  
**Branch:** `main`

## Runtime

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `rescue_agent_router_status` | **disabled_by_profile** |
| `router_registry_summary` | registered=0, disabled_by_profile=5, import_failed=0 |

## Services

| Service | Status |
|---------|--------|
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |

## Rescue-Agent-Routen (release)

| Route | HTTP | Code |
|-------|------|------|
| `GET /api/rescue-agent/sessions` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `POST /api/rescue-agent/register` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `POST /api/rescue-agent/system-report` | 404 | `PROFILE_ROUTE_BLOCKED` |

## Bewertung

| Feld | Wert |
|------|------|
| **`release_blocks_rescue_agent_expected`** | **true** |
| **Kein Fehler** | Profil-Gate blockiert Router korrekt |

## Gates

| Skript | Exit |
|--------|------|
| `check-runtime-profile-deploy-gate.sh` | 0 |
| `check-runtime-deploy-gate.sh` | 20 (legacy, erwartbar) |
