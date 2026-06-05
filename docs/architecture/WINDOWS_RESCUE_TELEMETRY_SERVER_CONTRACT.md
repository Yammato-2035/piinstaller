# Windows Rescue Telemetry Server Contract

**Track:** `windows-laptop-rescue-inspect`  
**Payload kind:** `windows_rescue_inspect`  
**Privacy default:** `diagnostic_metadata` (keine Dateiinhalte)

## Endpoint

```http
POST /api/rescue/windows-inspect
Content-Type: application/json
X-Setuphelfer-Run-Id: <run_id>
X-Setuphelfer-Payload-Hash: <sha256>
```

TLS required. No credentials in repository or evidence files.

## Success response

```json
{
  "status": "acknowledged",
  "ack_id": "string",
  "received_at": "string",
  "payload_hash_sha256": "string",
  "schema_version": "1.0.0"
}
```

## Completion rule

Inspect run is **green** only when:

- `inspect_report_created = true`
- `telemetry_transport.status = acknowledged`
- `server_ack_id` present
- `payload_hash_sha256` matches server-confirmed hash

Otherwise: `yellow` / `telemetry_not_delivered` or `red` on hash mismatch.

## Store-and-forward (concept)

Queue path (no secrets):

- `/var/lib/setuphelfer-rescue/telemetry-queue/`
- or `/run/setuphelfer-rescue/telemetry-queue/` (live session)

On network failure: `TELEMETRY-QUEUE-001`, status `queued_local`, retry plan.

## Error codes

| Code | Meaning |
|------|---------|
| `TELEMETRY-NETWORK-001` | Server unreachable |
| `TELEMETRY-AUTH-001` | Auth missing/invalid |
| `TELEMETRY-SCHEMA-001` | Invalid payload |
| `TELEMETRY-ACK-001` | Response without valid ack |
| `TELEMETRY-HASH-001` | Server confirmed different hash |
| `TELEMETRY-QUEUE-001` | Local queue created |
| `TELEMETRY-QUEUE-002` | Queue retry required |
| `TELEMETRY-PRIVACY-001` | Too much personal data |
| `TELEMETRY-CONSENT-001` | Operator consent missing |

## Forbidden in telemetry channel

File contents, cookies, tokens, passwords, private keys, unmasked serials (unless explicitly approved).

Backup/file data uses separate backup/cloud process.

Schema: `docs/evidence/windows-rescue/windows_rescue_telemetry.schema.json`

Operator ingest: `ingest_operator_hardware_run()` reads `operator_windows_readonly_plan_latest.json`; without plan → `awaiting_operator_hardware_run`. Green only with ACK + hash match.

Hard telemetry statuses: `not_created`, `queued_local`, `sent_no_ack`, `acknowledged`, `hash_mismatch`, `failed`.
