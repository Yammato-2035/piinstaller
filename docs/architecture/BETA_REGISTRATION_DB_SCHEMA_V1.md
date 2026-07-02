# Beta Registration Database Schema V1

**Version:** 1.0 · **SQL reference:** `docs/architecture/sql/beta_registration_schema_v1.sql`  
**Server:** Beta Registration (private) — mock port 8100

---

## 1. Design principles

- **Identity-light:** email hashed for lookup; no identity document columns.  
- **No telemetry payloads:** registration DB does not store full `system_assessment` blobs.  
- **Stick registry** is authoritative for `stick_id` → key mapping.  
- **MFA and agreement** gates drive `upload_allowed` responses to TS.

---

## 2. Entity relationship (logical)

```
beta_accounts ──┬── beta_agreements
                ├── beta_stick_registry
                ├── beta_machines
                └── beta_activation_tokens

beta_machines ──── machine_approval_audit
```

---

## 3. Table summaries

### `beta_accounts`

| Column | Type | Notes |
|--------|------|-------|
| `account_id` | UUID PK | Opaque |
| `email_hash` | VARCHAR(64) | SHA-256 of normalized email |
| `email_verified_at` | TIMESTAMPTZ | NULL until verified |
| `mfa_enabled` | BOOLEAN | Required for upload |
| `status` | ENUM | `active`, `restricted`, `revoked` |
| `created_at` | TIMESTAMPTZ | |

### `beta_agreements`

| Column | Type | Notes |
|--------|------|-------|
| `agreement_id` | UUID PK | |
| `account_id` | UUID FK | |
| `version` | VARCHAR(32) | e.g. `beta-2026-07` |
| `status` | ENUM | `missing`, `pending`, `valid`, `expired`, `revoked` |
| `telemetry_consent` | BOOLEAN | Explicit opt-in |
| `signed_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | Optional |

### `beta_stick_registry`

| Column | Type | Notes |
|--------|------|-------|
| `stick_id` | VARCHAR(64) PK | |
| `stick_type` | ENUM | `team_provisioned`, `registered_iso` |
| `account_id` | UUID FK nullable | Type B required |
| `device_public_key_id` | VARCHAR(64) | |
| `attestation_mode` | ENUM | `hmac`, `signature` |
| `status` | ENUM | `provisioned`, `active`, `revoked`, `expired` |
| `team_batch_id` | VARCHAR(64) | Type A |
| `iso_build_id` | VARCHAR(64) | Type B |
| `created_at` | TIMESTAMPTZ | |

### `beta_machines`

| Column | Type | Notes |
|--------|------|-------|
| `machine_fingerprint` | VARCHAR(128) PK | |
| `account_id` | UUID FK | |
| `stick_id` | VARCHAR(64) FK | Last seen stick |
| `approval_status` | ENUM | `unknown`, `pending`, `approved`, `blocked`, `revoked` |
| `first_seen_at` | TIMESTAMPTZ | |
| `last_seen_at` | TIMESTAMPTZ | |

### `beta_activation_tokens` — `token_hash`, `account_id`, `iso_build_id`, `expires_at`, `consumed_at`

### `machine_approval_audit` — `machine_fingerprint`, `from_status`, `to_status`, `operator_id`, `reason`, `created_at`

---

## 4. Internal API data sources

| Endpoint | Tables read |
|----------|-------------|
| `GET /public/v1/beta/status` | config only |
| `POST …/register` | `beta_accounts` insert |
| `POST …/sticks/activate` | tokens, registry, machines |
| `POST …/internal/v1/sticks/check-upload-permission` | agreements, sticks, machines |

---

## 5. Indexes (recommended)

- `beta_accounts(email_hash)` UNIQUE  
- `beta_machines(approval_status)` WHERE `pending`  
- `beta_stick_registry(status)`  
- `beta_activation_tokens(expires_at)` for cleanup job

---

## 6. Retention and references

Token cleanup after 7 days; revoked accounts soft-delete; audit log ≥ 2 years. DDL: `sql/beta_registration_schema_v1.sql`. See `beta_stick_registry.schema.json`, `BETA_STICK_REGISTRATION_AND_ATTESTATION_V1.md`.
