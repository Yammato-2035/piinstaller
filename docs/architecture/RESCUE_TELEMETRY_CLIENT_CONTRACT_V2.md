# Rescue Telemetry Client Contract V2

**Version:** 2.0 · **Schema ID:** `telemetry.rescue.beta.v2`  
**Implementation:** `backend/core/rescue_telemetry_client_contract_v2.py`  
**JSON Schema:** `docs/architecture/telemetry_rescue_beta_v2.schema.json`

---

## 1. Scope

This contract defines the **only** envelope Rescue Stick clients may send to beta telemetry ingest endpoints. It is public-safe: no secrets, no PII fields, strict privacy booleans.

---

## 2. Required top-level keys

| Key | Type | Description |
|-----|------|-------------|
| `schema_version` | const | Must be `telemetry.rescue.beta.v2` |
| `event_id` | UUID string | Unique per upload attempt |
| `created_at` | ISO8601 UTC | Generation timestamp |
| `rescue_version` | string | Rescue image version |
| `build_id` | string | CI/build correlation |
| `boot_session_id` | string | Per-boot identifier |
| `stick` | object | Stick identity + attestation |
| `beta` | object | Account/agreement flags |
| `machine` | object | Fingerprint + approval |
| `system_assessment` | object | Redacted assessment blob |
| `privacy` | object | Redaction attestation |

---

## 3–6. Nested objects (summary)

**Stick:** `stick_id`, `stick_type` (`team_provisioned`|`registered_iso`|`mock`), `device_public_key_id`, `attestation_mode`.  
**Beta:** `account_status`, `agreement_status`, `upload_allowed`.  
**Machine:** `machine_fingerprint`, `approval_status` (`pending`|`approved`|…).  
**Privacy:** all `contains_*` must be `false`; `redaction_version` e.g. `assessment.redaction.v2`.

---

## 7. Upload modes

Enum `TelemetryUploadMode`:

| Mode | Network upload |
|------|----------------|
| `disabled` | Never |
| `dry_run_local` | Local validation only |
| `mock_server` | Lab mock :8101 |
| `dev_laptop_lab` | Dev profile |
| `beta_server_quarantine` | Yes → quarantine bucket |
| `beta_server_accepted` | Yes → accepted path |

`upload_allowed_for_mode(mode, stick_verified, agreement_valid)` returns `(bool, reason)`.

---

## 8. HTTP mapping (client expectations)

| Endpoint | Method | Success codes |
|----------|--------|---------------|
| `/v1/telemetry/dry-run` | POST | 200 `dry_run_ok` |
| `/v1/telemetry/ingest` | POST | 200 accepted, 202 quarantine, 400/403 reject |

Client must treat **202** as spooled server-side, not as failure to retry.

---

## 9. Validation, signing, helpers

- `build_telemetry_payload_v2(...)` — test skeleton; production fills `system_assessment` after redaction.  
- `validate_telemetry_payload_v2(payload)` — empty list = OK; common errors: `schema_version_mismatch`, `missing:*`, `forbidden_privacy:*`.  
- Signing: `rescue_telemetry_signing_v1.py` (canonical JSON bytes; keys private).

Schemas: `telemetry_rescue_beta_v2.schema.json`, `telemetry_server_ingest_contract_v1.schema.json`.
