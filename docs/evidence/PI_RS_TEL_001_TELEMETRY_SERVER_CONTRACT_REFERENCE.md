# PI-RS-TEL-001 — TEL-012 Telemetry Server Contract Reference

Read-only inventory for the piinstaller Rescue Stick lab telemetry send flow.

## Server repository

| Field | Value |
|-------|-------|
| Path | `/home/volker/setuphelfer-private/setuphelfer-telemetry-server` |
| Branch | `tel-012-rescue-stick-lab-client-dual-source-dashboard` |
| Commit | `62e1b43` |
| Evidence | `docs/evidence/tel_012_rescue_stick_lab_client_dual_source_dashboard/` |

## Expected lab client (TEL-012)

| Field | Value |
|-------|-------|
| Client ID | `fake-rescue-stick-lab-client` |
| Product | `setuphelfer-rescue-stick` |
| Source | `rescue_stick_lab_preview` |
| Environment | `lab` |
| Payload kind (server wire) | `rescue_stick_lab_preview` |
| Payload kind (PI-RS-TEL-001 model) | `rescue_preview` |
| Secret env ref | `SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET` |

## HMAC-v2 ingest contract

- Endpoint (cloud, default): `POST {SETUPHELPER_TELEMETRY_LAB_BASE_URL}/v1/telemetry/ingest`
- Endpoint (legacy LAN lab): `POST {SETUPHELPER_TELEMETRY_LAB_BASE_URL}/api/telemetry/ingest` with `SETUPHELPER_TELEMETRY_LAB_PATH_STYLE=legacy`
- Canonical base: `https://telemetrie.setuphelfer.de` (`config/rescue_telemetry_endpoints.json`)
- Headers: `X-Setuphelfer-Timestamp`, `X-Setuphelfer-Signature`, `X-Setuphelfer-Client-Id`, `X-Setuphelfer-Nonce`
- Signature message: `{timestamp}.{nonce}.{raw_json_body_bytes}`
- Algorithm: HMAC-SHA256 hex digest

## Server responses (TEL-012)

| HTTP | reason_code (typical) | PI-RS-TEL-001 mapping |
|------|----------------------|------------------------|
| 202 | `accepted_rescue_lab_telemetry` | `accepted_rescue_lab_telemetry` |
| 401 | `invalid_signature`, `unknown_client`, `missing_client_id` | `rejected_auth` |
| 403 | `product_not_allowed`, `source_not_allowed`, `environment_not_allowed` | `rejected_product_source_or_environment` |
| 409 | `replay_nonce` | `replay_nonce` |

## Wire payload adapter

PI-RS-TEL-001 builds a simplified synthetic model (`rescue_preview` payload kind). Before send, `adapt_payload_for_tel012_ingest()` maps to the TEL-012 wire contract (`rescue_stick_lab_preview`) without adding host data.

## Next phase

**PI-RS-TEL-001** (this workspace) — first synthetic lab send flow from piinstaller.

**PI-RS-TEL-002** (planned) — Rescue Stick network-gated telemetry reachability + offline queue preview (no real replay queue yet).

## Contract availability

Status: **available** — server files read from telemetry-server workspace on 2026-07-05.
