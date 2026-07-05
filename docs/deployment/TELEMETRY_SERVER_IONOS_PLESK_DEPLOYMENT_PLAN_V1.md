# Telemetry Server IONOS Plesk Deployment Plan V1

**Version:** 1.0 · **Target:** `telemetry.setuphelfer.de`  
**Reference:** `TELEMETRY_SERVER_BETA_0_1.md`

---

## 1. Objective

Host the telemetry ingest service with strict **no-command** routing, PostgreSQL persistence, and outbound-only connectivity to beta registration and diagnostics servers.

---

## 2. Infrastructure layout

```
Internet ──► nginx (Plesk) ──► uvicorn :8201
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              PostgreSQL      BR internal      DS import URL
              telemetry_db    permission API   (mTLS/bearer)
```

---

## 3. DNS and TLS

| Record | Value |
|--------|-------|
| `telemetry.setuphelfer.de` | A/AAAA to VPS IP |
| TLS | Let’s Encrypt auto-renew via Plesk |

Stick clients pin to this hostname in rescue build config (private overlay).

---

## 4. Plesk configuration

1. Create subdomain `telemetry.setuphelfer.de`.  
2. **Disable** PHP and WordPress for this vhost.  
3. nginx location blocks:

```nginx
location / {
    proxy_pass http://127.0.0.1:8201;
    proxy_set_header Host $host;
    client_max_body_size 512k;
}

# Explicit deny — defense in depth
location ~ ^/(execute|command|shell|remote-help|fix|apply|write|mount|wipe|restore) {
    return 403;
}
```

4. Create DB `telemetry` and apply `sql/telemetry_server_schema_v1.sql`.  
5. Environment file `/etc/setuphelfer/telemetry-server.env`:

   - `TS_DATABASE_URL`  
   - `TS_BR_INTERNAL_URL=https://beta.setuphelfer.de`  
   - `TS_DS_FORWARD_URL=https://diagnose.setuphelfer.de/v1/learning/import`  
   - `TS_SIGNING_KEYRING_PATH=/etc/setuphelfer/telemetry-keys.json` (chmod 600)  
   - `TS_QUARANTINE_RETENTION_DAYS=14`

---

## 5. systemd unit

```ini
[Service]
ExecStart=/opt/setuphelfer-telemetry-server/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8201
EnvironmentFile=/etc/setuphelfer/telemetry-server.env
```

---

## 6. Network policy

| Direction | Allow |
|-----------|-------|
| Inbound 443 | World (ingest only) |
| Outbound 443 | `beta.setuphelfer.de`, `diagnose.setuphelfer.de` |
| Outbound other | Deny by default |

No SSH from internet; admin via Plesk panel or VPN.

---

## 7. Verification checklist

```bash
curl -sS https://telemetry.setuphelfer.de/v1/telemetry/health
curl -sS -X POST https://telemetry.setuphelfer.de/v1/telemetry/dry-run \
  -H 'Content-Type: application/json' -d @fixtures/minimal_envelope.json
```

Expect `403` on forbidden paths (mirror mock v2 tests).

---

## 8. Monitoring

- Uptime check on `/health` every 60s.  
- Alert if quarantine table row count > 10k.  
- Alert if forward outbox `attempts` > 5 for any row.

---

## 9. Scaling (beta phase)

Single VPS sufficient for ≤500 sticks. Horizontal scaling deferred until post-beta; sticky sessions not required (stateless ingest).

---

## 10. Related documents

- `TELEMETRY_SERVER_DB_SCHEMA_V1.md`  
- `BETA_DATA_FLOW_V1.md`  
- `DIAGNOSTICS_SERVER_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`
