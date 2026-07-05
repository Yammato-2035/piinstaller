# Diagnostics Server IONOS Plesk Deployment Plan V1

**Version:** 1.0 · **Target:** `diagnose.setuphelfer.de`  
**Reference:** `DIAGNOSTICS_SERVER_HARDWARE_DB_BETA_0_1.md`

---

## 1. Objective

Deploy the diagnostics hardware database and learning import API on a **private** subdomain with no public stick-facing routes.

---

## 2. Access model

| Caller | Access |
|--------|--------|
| Telemetry Server | `POST /v1/learning/import` (service token) |
| Operator VPN | Review queue UI (private) |
| Public internet | **Denied** except `/health` from monitors |

Implement IP allowlist or mTLS for import endpoint.

---

## 3. Plesk setup

1. Subdomain `diagnose.setuphelfer.de`.  
2. Reverse proxy to app on `127.0.0.1:8202`.  
3. PostgreSQL database `diagnostics_hw`.  
4. Apply `sql/diagnostics_hardware_db_schema_v1.sql`.  
5. Environment `/etc/setuphelfer/diagnostics-server.env`:

   - `DS_DATABASE_URL`  
   - `DS_IMPORT_BEARER_TOKEN` (shared with TS, rotated)  
   - `DS_ALLOWED_SOURCE_IPS` (TS egress IPs)  
   - `DS_REVIEW_WEBHOOK` (optional OP notify)

---

## 4. nginx hardening

```nginx
location /v1/learning/import {
    allow <telemetry-server-ip>;
    deny all;
    proxy_pass http://127.0.0.1:8202;
}

location /health {
    allow all;
    proxy_pass http://127.0.0.1:8202;
}
```

---

## 5. Application service

```ini
[Service]
ExecStart=/opt/setuphelfer-diagnostics-server/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8202
EnvironmentFile=/etc/setuphelfer/diagnostics-server.env
```

---

## 6. Data protection

- JSONB payloads encrypted at rest (Postgres TDE or volume encryption).  
- Daily backup via Plesk; 30-day retention.  
- PII rejection logs stored without raw payload copy.

---

## 7. Verification

```bash
# From TS subnet only:
curl -sS -X POST https://diagnose.setuphelfer.de/v1/learning/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @fixtures/learning_import_minimal.json
```

Expect `import_status: accepted` with `review_required: true`.

Test PII rejection with fixture containing `email` key → `422`.

---

## 8. Operator review UI

Deploy on separate path `/internal/` behind VPN + MFA (not on public internet). Lists `hardware_review_queue` pending rows.

---

## 9. Rollback

Restore DB snapshot + previous container. Re-run import audit to detect duplicate `event_id` (idempotent upsert).

---

## 10. Related documents

- `hardware_db_schema_v1.json`  
- `diagnostics_learning_import_contract_v1.schema.json`  
- `TELEMETRY_SERVER_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`
