# Rescue-Agent Ingest — OpenAPI / Contract Check (read-only)

**Stand:** 2026-06-02  
**Profil:** `release` (Router deaktiviert)

## OpenAPI unter release

`/api/rescue-agent/*` erscheint **nicht** in `openapi.json`, solange `rescue_agent_router_status=disabled_by_profile`. Das ist erwartbar (Router nicht registriert).

Legacy `/api/rescue/*` und Deploy-Rescue-Pfade sind vorhanden — **nicht** Teil des Rescue-Agent-Stubs.

## Contract (Quellcode `backend/rescue_agent/routers.py`)

| Methode | Pfad | Rolle |
|---------|------|--------|
| POST | `/api/rescue-agent/discovery/preview` | Discovery-Preview + nftables_preview |
| POST | `/api/rescue-agent/register` | Pairing-Stub (`local_lab` only) |
| POST | `/api/rescue-agent/heartbeat` | Session-Heartbeat |
| POST | `/api/rescue-agent/system-report` | Report-Ingest (E2EE oder test_mode) |
| GET | `/api/rescue-agent/sessions` | Session-Liste |
| GET | `/api/rescue-agent/sessions/{session_id}` | Session-Detail |

## Profil-Gates

| Profil | Verhalten |
|--------|-----------|
| `release` | Router **nicht** registriert → `PROFILE_ROUTE_BLOCKED` (Middleware) |
| `local_lab` | Router registriert; Register erlaubt; Release-Register → 403 `RESCUE_AGENT_REGISTRATION_DISABLED_IN_RELEASE` |

## E2EE

**`contract_stub_only`** — `RESCUE_AGENT_E2EE_REQUIRED` ohne `encrypted_envelope` und ohne `test_mode_allow_unencrypted=true`. Stub-Envelope via `build_encrypted_envelope`.

## nftables

**`preview_only_apply_false`** — `build_nftables_policy_preview()` setzt `apply_allowed: false`; nur `commands_preview`, kein Apply-Endpoint.

## Verbotene Routen

Kein `/apply`, `/execute`, `/install`, `/write` unter `/api/rescue-agent/*` (Unit-Test `test_forbidden_apply_execute_install_write_routes_not_present`).

## Unit-Contract (Workspace, nicht Live)

`backend/tests/test_rescue_agent_api_contract_v1.py` — Register, E2EE-Block, Session-403, test_mode-Pfad.
