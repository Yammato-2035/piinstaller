# Profile Router Gate — Ergebnis

**Datum:** 2026-05-31

## Mechanismen

1. **Bedingte `include_router`** in `backend/app.py` für fleet, dev-diagnostics, rescue-remote, dev-server
2. **Middleware** `install_profile_route_gate_middleware` — 404 `PROFILE_ROUTE_BLOCKED` für nicht erlaubte Pfade (inkl. Dev-Dashboard-Routen auf `app`)
3. **Capability-Delegation** in `fleet_session_state`, `dev_diagnostic_export`, `rescue_remote.service`

## Release-Profil

| Route-Präfix | Registriert | Middleware |
|--------------|-------------|------------|
| `/api/fleet` | nein | blockiert |
| `/api/dev-diagnostics` | nein | blockiert |
| `/api/rescue-remote` | nein | blockiert |
| `/api/dev-dashboard` | blockiert via Middleware | ja |
| `/api/dev-server` | nein | blockiert |

## Local-Lab-Profil

Alle obigen Dev-Routen registrierbar; Rescue Remote ohne Write-Runbooks.

## Tests

- `backend/tests/test_profile_router_registration_v1.py` — 3/3 OK
- `backend/tests/test_install_profile_gate_v1.py` — Audit red bei Release+Fleet in OpenAPI

## `/api/version`

`profile_gate_audit_route_paths` setzt `profile_gate_status` auf red bei `release_profile_dev_routes_visible`.
