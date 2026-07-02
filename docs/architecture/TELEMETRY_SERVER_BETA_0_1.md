# Telemetry Server Beta 0.1

**Version:** beta.0.1 · **Mock:** `backend/dev/telemetry_mock_server_v2.py` (port 8101)  
**Private implementation:** `setuphelfer-telemetry-server` repository

---

## 1. Role

The telemetry server is the **only** internet-facing ingest point for Rescue Stick envelopes. It validates schema, authenticates sticks, applies quarantine policy, persists events, and forwards accepted payloads to the diagnostics server.

It does **not** implement remote repair, shell access, or stick callbacks.

---

## 2. Service boundaries

| In scope | Out of scope |
|----------|--------------|
| POST ingest / dry-run | Command execution |
| Stick signature verify | User registration UI |
| Quarantine + accepted stores | Hardware learning rules |
| Forward outbox to DS | Operator approval UI |
| Health endpoints | Email delivery |

---

## 3. HTTP surface (beta.0.1)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Liveness |
| GET | `/v1/telemetry/health` | None | Versioned health |
| POST | `/v1/telemetry/dry-run` | Stick sig optional | Schema check |
| POST | `/v1/telemetry/ingest` | Stick sig required | Main ingest |

### Forbidden prefixes (403)

`/execute`, `/command`, `/shell`, `/remote-help`, `/fix`, `/apply`, `/write`, `/mount`, `/wipe`, `/restore`

---

## 4. Ingest decision tree

```
ingest request
  ├─ schema invalid → 400 rejected_schema
  ├─ stick unknown/revoked → 403 rejected_auth
  ├─ agreement invalid → 202 quarantine_pending_agreement
  ├─ machine not approved → 202 quarantine_pending_approval
  └─ OK → 200 accepted (+ forward outbox)
```

Response fields (accepted path): `accepted`, `status`, `event_id`, `redaction_applied`, `diagnostics_forwarded`, `learning_export_allowed`.

---

## 5. Dependencies

| Dependency | Use |
|------------|-----|
| Beta Registration | `check-upload-permission` internal API |
| PostgreSQL | Event + quarantine tables |
| Object storage (optional) | Large assessment attachments (future) |
| Diagnostics Server | Learning import POST |

---

## 6. Configuration (environment)

| Variable | Purpose |
|----------|---------|
| `TS_DATABASE_URL` | Postgres connection |
| `TS_BR_INTERNAL_URL` | Beta registration base |
| `TS_DS_FORWARD_URL` | Diagnostics import endpoint |
| `TS_SIGNING_KEYS` | JSON keyring ref (not in git) |
| `TS_QUARANTINE_RETENTION_DAYS` | Default 14 for agreement missing |

---

## 7. Observability

- Structured logs: `event_id`, `stick_id`, `status`, no payload PII.  
- Metrics: ingest rate, quarantine depth, forward lag.  
- Alerts: forward outbox age > 1h, quarantine growth anomaly.

---

## 8. Deployment target

Production: `telemetry.setuphelfer.de` on IONOS Plesk — see `TELEMETRY_SERVER_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`.

Lab: `127.0.0.1:8101` mock — no persistence.

---

## 9. Schema references

- Client envelope: `telemetry.rescue.beta.v2`  
- Server ingest wrapper: `telemetry_server_ingest_contract_v1.schema.json`  
- SQL: `sql/telemetry_server_schema_v1.sql`

---

## 10. Related documents

- `RESCUE_TELEMETRY_CLIENT_CONTRACT_V2.md`  
- `BETA_DATA_FLOW_V1.md`  
- `SERVICE_INTERACTION_MATRIX_V1.md`
