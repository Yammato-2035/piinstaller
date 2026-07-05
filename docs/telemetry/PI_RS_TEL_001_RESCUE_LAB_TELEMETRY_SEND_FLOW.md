# PI-RS-TEL-001 — Rescue Stick Lab Telemetry Send Flow

## Scope

Lab-only synthetic telemetry from the piinstaller / SetupHelfer Rescue Stick workspace to the private telemetry server prepared in TEL-012.

**Not in scope:** production telemetry, real host data, automatic send on startup, backup/restore/USB writes.

## Client identity

| Field | Value |
|-------|-------|
| Client ID | `fake-rescue-stick-lab-client` |
| Product | `setuphelfer-rescue-stick` |
| Source | `rescue_stick_lab_preview` |
| Environment | `lab` |
| Payload kind (model) | `rescue_preview` |
| Payload kind (TEL-012 wire) | `rescue_stick_lab_preview` |

## Configuration (environment only)

| Variable | Purpose |
|----------|---------|
| `SETUPHELPER_TELEMETRY_LAB_BASE_URL` | Lab telemetry server base URL |
| `SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_ID` | Client ID (default: `fake-rescue-stick-lab-client`) |
| `SETUPHELPER_LAB_CLIENT_FAKE_RESCUE_STICK_SECRET` | HMAC secret — **no default in code** |

If the secret is missing, send is blocked with `blocked_missing_secret`.

## API (lab profile only)

| Method | Path | Profile |
|--------|------|---------|
| `GET` | `/api/rescue/telemetry/lab/status` | `developer`, `local_lab`, `rescue_lab` |
| `POST` | `/api/rescue/telemetry/lab/send-preview` | same |

Release/production profile returns HTTP 403 `feature_disabled`.

## HMAC-v2 signing

- Nonce: UUID v4 per request
- Timestamp: Unix seconds
- Body: JSON serialization matching TEL-012 ingest tests
- Replay: server returns HTTP 409 `replay_nonce`

## Safety

- PII validator blocks MAC, IP, hostname, email, raw logs, secrets, cross-cloudserver payloads
- `production_ready` is always `false`
- HMAC success means **lab acceptance only**, not production release

## Evidence

`docs/evidence/pi_rs_tel_001_rescue_lab_telemetry_send_flow/`

## Next phase

**PI-RS-TEL-002** — Rescue Stick network-gated telemetry reachability + offline queue preview (roadmap only; no real offline replay queue in PI-RS-TEL-001).
