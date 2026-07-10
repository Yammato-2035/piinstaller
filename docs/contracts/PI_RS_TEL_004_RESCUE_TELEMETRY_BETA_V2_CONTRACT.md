# PI-RS-TEL-004 — Rescue Telemetry beta.v2 Contract

**Schema:** `telemetry.rescue.beta.v2`
**Sprint:** PI-RS-TEL-004
**Status:** Preview-only (`production_ready=false`)

## Purpose

Migrate rescue-stick telemetry preview from legacy `rescue_boot_network_telemetry` (schema v1, LAN proxy) to the IONOS cloud contract `telemetry.rescue.beta.v2`.

## Required top-level fields

| Field | Requirement |
|-------|-------------|
| `schema_version` | Must be `telemetry.rescue.beta.v2` |
| `event_id` | UUID |
| `created_at` | ISO-8601 UTC |
| `rescue_version` | Workspace project version |
| `build_id` | Short build/payload identifier (hashed prefix) |
| `boot_session_id` | Hashed boot session token |
| `stick` | Stick metadata (`stick_type` mock until provisioned) |
| `beta` | `upload_allowed=false` until operator agreement |
| `machine` | Hashed fingerprint only |
| `system_assessment` | Preview aggregates, no raw logs |
| `privacy` | All `contains_*` flags must be `false` |

## PI-RS-TEL-004 preview extensions

Allowed under `system_assessment` (additional properties):

- `source_kind`: `rescue_stick`
- `event_kind`: `telemetry.rescue.beta.v2`
- `production_ready`: `false`
- `preview_only`: `true`
- `operator_approval_required`: `true`
- `external_calls`: `false` (default)
- `cloud_send_requires_operator_consent`: `true`
- `device`, `session`, `build`, `network`, `diagnostics_aggregates`

## Forbidden

- MAC/IP/hostname/email in plaintext
- Raw logs (`dmesg`, `journal`, `lspci`, `lsusb`)
- Secrets, API keys, Authorization headers
- `production_ready=true` in preview path

## Endpoints (cloud default)

| Kind | URL |
|------|-----|
| Health | `https://telemetrie.setuphelfer.de/v1/telemetry/health` |
| Ingest | `https://telemetrie.setuphelfer.de/v1/telemetry/ingest` |

Canonical config: `config/rescue_telemetry_endpoints.json`

## Legacy (lab override only)

`SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=legacy` → `/api/rescue/telemetry/*` on LAN proxy.

## Implementation

- Payload builder: `backend/core/rescue_telemetry_payload_v2.py`
- Schema reference: `docs/architecture/telemetry_rescue_beta_v2.schema.json`
- Auth gate: `backend/core/rescue_telemetry_auth_gate.py`
