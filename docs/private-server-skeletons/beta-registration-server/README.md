# Beta Registration Server — Private Skeleton

**Purpose:** Describe the expected layout of the private `setuphelfer-beta-registration` repository.  
**This directory contains no secrets, no production keys, and no runnable server code.**

---

## 1. Repository role

The beta registration server owns:

- User signup, email verification, MFA enrollment  
- Beta agreement and telemetry consent records  
- Stick registry (`team_provisioned`, `registered_iso`)  
- Type B activation token issuance  
- Internal `check-upload-permission` API for the telemetry server  
- Machine fingerprint registry (approval status source of truth for BR)

Public repo provides contracts, SQL reference, and mock on port **8100**.

---

## 2. Expected directory layout

```
setuphelfer-beta-registration/
├── README.md                    # Deploy + env var names (no values)
├── pyproject.toml               # Python 3.11+, FastAPI
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Settings from environment
│   ├── db/
│   │   ├── session.py
│   │   └── migrations/          # Alembic revisions → beta_registration_schema_v1
│   ├── routers/
│   │   ├── health.py
│   │   ├── public_beta.py       # /public/v1/beta/*
│   │   ├── sticks.py            # activate, registry
│   │   └── internal.py          # /internal/v1/sticks/check-upload-permission
│   ├── services/
│   │   ├── agreement_gate.py    # Mirror beta_agreement_gate_v1 rules
│   │   ├── stick_registry.py
│   │   └── activation.py
│   └── models/                  # SQLAlchemy ORM
├── tests/
│   ├── test_mock_parity_8100.py # Same routes as backend/dev mock
│   └── test_agreement_gate.py
├── deploy/
│   ├── systemd/
│   │   └── setuphelfer-beta-registration.service
│   └── nginx/
│       └── beta.setuphelfer.de.conf.snippet
└── contracts/
    └── beta_stick_registry.schema.json  # Submodule or copy from public repo
```

---

## 3. Environment variables (names only)

| Variable | Purpose |
|----------|---------|
| `BR_DATABASE_URL` | PostgreSQL connection string |
| `BR_SESSION_SECRET` | Session signing |
| `BR_MFA_ISSUER` | TOTP issuer label |
| `BR_PUBLIC_BASE_URL` | e.g. `https://beta.setuphelfer.de` |
| `BR_SMTP_*` | Email verification (host, port, user — set on server) |
| `BR_INTERNAL_API_TOKEN` | Telemetry server → internal routes |

**Never commit values.** Use Plesk environment UI or `/etc/setuphelfer/beta-registration.env`.

---

## 4. Contract alignment

| Public artifact | Skeleton usage |
|-----------------|----------------|
| `docs/architecture/sql/beta_registration_schema_v1.sql` | Initial migration |
| `docs/architecture/beta_stick_registry.schema.json` | Request/response validation |
| `backend/core/beta_agreement_gate_v1.py` | Port logic to `agreement_gate.py` |
| `backend/core/beta_machine_approval_contract_v1.py` | Machine status transitions |
| `backend/dev/beta_registration_mock_server_v1.py` | Parity tests (port 8100) |

---

## 5. API surface (minimum)

| Method | Path |
|--------|------|
| GET | `/health` |
| GET | `/public/v1/beta/status` |
| POST | `/public/v1/beta/register` |
| POST | `/public/v1/sticks/activate` |
| POST | `/internal/v1/sticks/check-upload-permission` |

Internal routes require `Authorization: Bearer` service token.

---

## 6. Deployment reference

Follow `docs/deployment/BETA_PORTAL_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`:

- uvicorn on `127.0.0.1:8200`  
- nginx TLS termination on Plesk  
- PostgreSQL database from reference SQL

---

## 7. Security checklist

- [ ] Rate limits on register and activate  
- [ ] No identity document fields accepted (`FORBIDDEN_ID_DOCUMENT_FIELDS`)  
- [ ] Email stored as hash only in primary lookup column  
- [ ] Activation tokens single-use, short TTL  
- [ ] CORS restricted to beta portal origin  

References: `BETA_REGISTRATION_DB_SCHEMA_V1.md`, `beta_stick_activation_flow.md`, `PUBLIC_PRIVATE_BOUNDARY_V1.md`.
