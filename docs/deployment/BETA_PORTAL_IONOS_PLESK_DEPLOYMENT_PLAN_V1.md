# Beta Portal IONOS Plesk Deployment Plan V1

**Version:** 1.0 · **Target:** `beta.setuphelfer.de`  
**Component:** Beta Registration Server (private)

---

## 1. Objective

Deploy the beta registration API and static portal UI on IONOS managed hosting with Plesk, isolated from telemetry and diagnostics subdomains.

---

## 2. Prerequisites

| Item | Status |
|------|--------|
| Private repo `setuphelfer-beta-registration` built | Required |
| DNS A/AAAA record `beta.setuphelfer.de` | Required |
| Plesk subscription with PHP disabled for this vhost | Recommended |
| PostgreSQL database (Plesk extension or external) | Required |
| TLS certificate (Let’s Encrypt via Plesk) | Required |

---

## 3. Plesk setup steps

1. **Add subdomain** `beta` under `setuphelfer.de` subscription.  
2. **Document root:** `/var/www/vhosts/setuphelfer.de/beta.setuphelfer.de/app/public` (static) or reverse proxy only.  
3. **Enable Docker / Node / Python** extension per stack choice (FastAPI + uvicorn behind nginx recommended).  
4. **Create database** `beta_registration` + user with least privilege.  
5. **Apply SQL** from `docs/architecture/sql/beta_registration_schema_v1.sql`.  
6. **Environment variables** (Plesk “Environment Variables” UI — values NOT in git):

   - `BR_DATABASE_URL`  
   - `BR_SESSION_SECRET` (rotate per environment)  
   - `BR_MFA_ISSUER=Setuphelfer Beta`  
   - `BR_PUBLIC_BASE_URL=https://beta.setuphelfer.de`  
   - `BR_CORS_ORIGINS=https://beta.setuphelfer.de`

7. **Configure reverse proxy** `/` → `127.0.0.1:8200` (app port).  
8. **Enable HTTP→HTTPS redirect** and HSTS (max-age 31536000 after smoke test).

---

## 4. systemd / process manager

On Plesk-managed VPS (root access):

```ini
# /etc/systemd/system/setuphelfer-beta-registration.service
[Unit]
Description=Setuphelfer Beta Registration
After=network.target postgresql.service

[Service]
Type=simple
User=beta-reg
WorkingDirectory=/opt/setuphelfer-beta-registration
EnvironmentFile=/etc/setuphelfer/beta-registration.env
ExecStart=/opt/setuphelfer-beta-registration/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8200
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 5. Post-deploy verification

| Check | Command / URL |
|-------|----------------|
| Health | `curl -sS https://beta.setuphelfer.de/health` |
| Public status | `curl -sS https://beta.setuphelfer.de/public/v1/beta/status` |
| TLS grade | SSL Labs test ≥ A |
| DB migration | App reports schema version |
| Mock parity | Compare responses with port 8100 mock |

---

## 6. Backup

- Plesk daily backup: files + DB.  
- Test restore quarterly on staging subdomain.

---

## 7. Security hardening

- Fail2ban on nginx auth endpoints.  
- Rate limit `/public/v1/*/register` and `/sticks/activate`.  
- No directory listing; deny `.env` and `*.sql` via nginx.

---

## 8. Rollback

1. Stop systemd unit.  
2. Restore previous release directory snapshot.  
3. Restore DB to pre-deploy dump if migration ran.  
4. Re-run health checks.

---

## 9. Related documents

- `BETA_REGISTRATION_DB_SCHEMA_V1.md`  
- `docs/private-server-skeletons/beta-registration-server/README.md`  
- `WORDPRESS_BETA_BRIDGE_DEPLOYMENT_PLAN_V1.md`
