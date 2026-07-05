# Telemetry Server Database Schema V1

**Version:** 1.0 · **SQL:** `docs/architecture/sql/telemetry_server_schema_v1.sql`  
**Service:** Telemetry Server beta.0.1

---

## 1. Overview

The telemetry database separates **quarantine**, **accepted**, and **forward outbox** data. Payloads are stored as JSONB with server-side encryption at rest (deploy responsibility).

---

## 2. Tables

### `telemetry_sticks_cache`

Read-through cache of BR stick registry (not authoritative).

| Column | Type | Description |
|--------|------|-------------|
| `stick_id` | VARCHAR(64) PK | |
| `device_public_key_id` | VARCHAR(64) | |
| `attestation_mode` | VARCHAR(16) | |
| `status` | VARCHAR(16) | |
| `synced_at` | TIMESTAMPTZ | |

### `telemetry_events_quarantine`

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | UUID PK | Client-supplied |
| `stick_id` | VARCHAR(64) | |
| `machine_fingerprint` | VARCHAR(128) | |
| `quarantine_reason` | VARCHAR(64) | e.g. `agreement_missing` |
| `payload_json` | JSONB | Full envelope |
| `created_at` | TIMESTAMPTZ | |
| `expires_at` | TIMESTAMPTZ | TTL cleanup |

### `telemetry_events_accepted`

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | UUID PK | |
| `stick_id` | VARCHAR(64) | |
| `machine_fingerprint` | VARCHAR(128) | |
| `rescue_version` | VARCHAR(32) | |
| `build_id` | VARCHAR(64) | |
| `ingest_status` | VARCHAR(32) | `accepted` |
| `payload_json` | JSONB | |
| `diagnostics_forwarded` | BOOLEAN | |
| `created_at` | TIMESTAMPTZ | |

### `telemetry_forward_outbox`

| Column | Type | Description |
|--------|------|-------------|
| `outbox_id` | BIGSERIAL PK | |
| `event_id` | UUID FK | |
| `target` | VARCHAR(64) | `diagnostics` |
| `attempts` | INT | |
| `last_error` | TEXT | |
| `next_retry_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ | |

### `telemetry_ingest_audit`

| Column | Type | Description |
|--------|------|-------------|
| `audit_id` | BIGSERIAL PK | |
| `event_id` | UUID | |
| `http_status` | INT | |
| `response_status` | VARCHAR(64) | |
| `created_at` | TIMESTAMPTZ | |

---

## 3. Jobs

| Job | Frequency | Action |
|-----|-----------|--------|
| Quarantine expiry | daily | Delete expired quarantine rows |
| Promotion | on BR webhook / 5 min | Move eligible quarantine → accepted |
| Forward worker | continuous | POST DS import, update outbox |
| Stick cache sync | 15 min | Pull BR registry deltas |

---

## 4. Indexes

```sql
CREATE INDEX idx_quarantine_reason ON telemetry_events_quarantine(quarantine_reason);
CREATE INDEX idx_quarantine_expires ON telemetry_events_quarantine(expires_at);
CREATE INDEX idx_accepted_stick ON telemetry_events_accepted(stick_id, created_at DESC);
CREATE INDEX idx_outbox_pending ON telemetry_forward_outbox(next_retry_at) WHERE completed_at IS NULL;
```

---

## 5. Size estimates (beta)

- ~5 KB per event JSONB  
- 100 beta users × 10 boots/month ≈ 5 MB/month + indexes  
- Plan 1 GB quota for beta phase

---

## 6. Backup

- Daily logical dump via Plesk backup manager.  
- No restore of quarantine expired rows into accepted without manual OP review.

---

## 7. Related documents

- `TELEMETRY_SERVER_BETA_0_1.md`  
- `telemetry_server_ingest_contract_v1.schema.json`  
- `BETA_DATA_FLOW_V1.md`
