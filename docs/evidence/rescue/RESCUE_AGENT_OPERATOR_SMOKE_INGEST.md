# Rescue-Agent Operator-Smoke — Ingest

**Stand:** 2026-06-02  
**Smoke-Dir:** `docs/evidence/rescue/rescue_agent_ingest_operator_smoke_20260602_182452`  
**Skript:** `scripts/rescue-live/rescue-agent-ingest-stub-smoke-operator.sh`  
**HEAD (Smoke):** `b908372`

## Bewertung

**`rescue_agent_ingest_stub_smoke_status=ok`**

## Release-Block vorher

**yes** — `POST /api/rescue-agent/register` → **404** `PROFILE_ROUTE_BLOCKED` unter `release`.

## local_lab

| Feld | Wert |
|------|------|
| `install_profile` | **local_lab** |
| `dev_control_enabled` | **true** |
| `rescue_agent_router_status` | **registered** |
| `router_registry_summary` | registered=5, import_failed=0 |
| **PROFILE_GUARD_OK** | **yes** |

## Rescue-Agent-Routen (OpenAPI, local_lab)

**6** Endpunkte sichtbar:

- `POST /api/rescue-agent/discovery/preview`
- `POST /api/rescue-agent/register`
- `POST /api/rescue-agent/heartbeat`
- `POST /api/rescue-agent/system-report`
- `GET /api/rescue-agent/sessions`
- `GET /api/rescue-agent/sessions/{session_id}`

## Negative Tests

| Test | HTTP | Code |
|------|------|------|
| ohne gültige Session (leer/invalid) | **403** | `RESCUE_AGENT_INVALID_SESSION` |
| unencrypted ohne `test_mode_allow_unencrypted` | **403** | `RESCUE_AGENT_INVALID_SESSION` |

Kein HTTP 500. Kein Secret-Leak in Responses.

## Registration Stub

| Feld | Wert |
|------|------|
| HTTP | **200** |
| `code` | `RESCUE_AGENT_REGISTER_OK` |
| `registration_status` | **pending** |
| `agent_id` | `ra-aa5354ea73d2` |
| `session_id` | `rescue-c73a719c` |

## Valid Stub System-Report

| Feld | Wert |
|------|------|
| HTTP | **200** |
| `code` | `RESCUE_AGENT_REPORT_ACCEPTED` |
| `session_id` | `rescue-c73a719c` |
| E2EE Envelope | **yes** — `envelope_version=1.0`, `alg=X25519-Ed25519-AEAD` |

## Release nach Trap

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |
| `rescue_agent_router_status` | **disabled_by_profile** |
| `router_registry_summary` | disabled_by_profile=5, import_failed=0 |
| `GET /api/rescue-agent/sessions` | **404** `PROFILE_ROUTE_BLOCKED` |

## Contract / Safety

| Thema | Status |
|-------|--------|
| E2EE | **contract_stub_only** (Envelope im Stub sichtbar) |
| nftables | **preview_only_apply_false** |
| Write/Apply-Routen | **no** |
| Rescue-Agent | Stub/Contract, kein Produktiv-Agent |

## Guards

Kein ISO-Build, QEMU, USB/dd, Backup, Restore, apt.

## Rohdaten

`raw/` unter Smoke-Dir (nicht committed — Referenz in JSON).
