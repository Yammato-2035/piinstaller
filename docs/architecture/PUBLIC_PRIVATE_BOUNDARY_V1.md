# Public vs Private Repository Boundary V1

**Version:** 1.0 · **Gate:** `scripts/check-public-private-boundary.sh`, `scripts/check-private-import-boundaries.sh`  
**Supersedes (naming):** Aligns with `PUBLIC_PRIVATE_MODULE_BOUNDARIES.md` for beta server rollout.

---

## 1. Principle

The **public** GitHub repository is open source and ships the Rescue Stick, local Setuphelfer backend, contracts, and documentation. **Private** repositories hold commercial server code, production configuration templates (without secrets in git), and operator tooling.

Dependency direction is **one-way**: private may depend on public contracts; public **never** imports private modules.

```
┌────────────────────────────────────────┐
│ PUBLIC REPO                            │
│ Contracts · Facades · Rescue ISO build │
│ Mock servers (8100–8102) · JSON Schema │
└─────────────────┬──────────────────────┘
                  │ read-only mirror / submodule
                  ▼
┌────────────────────────────────────────┐
│ PRIVATE REPOS                          │
│ beta-registration-server               │
│ telemetry-server                       │
│ diagnostics-server                     │
│ operator-dashboard · commercial        │
└────────────────────────────────────────┘
```

---

## 2. What stays public

| Category | Examples |
|----------|----------|
| Client contracts | `rescue_telemetry_client_contract_v2.py`, `beta_machine_approval_contract_v1.py` |
| JSON schemas | `telemetry_rescue_beta_v2.schema.json`, `beta_stick_registry.schema.json` |
| SQL reference | `docs/architecture/sql/*.sql` (structure only, no production data) |
| Architecture docs | This folder under `docs/architecture/` |
| Mock/dev servers | `backend/dev/*_mock_server_*.py` — lab ports only |
| Deployment **plans** | `docs/deployment/*_PLAN_V1.md` — no credentials |
| Skeleton README | `docs/private-server-skeletons/` — structure description only |

---

## 3. What is private-only

| Area | Private path (typical) | Public exposure |
|------|------------------------|-----------------|
| Beta registration API | `beta-registration-server/` | OpenAPI stub + mock only |
| Telemetry ingest store | `telemetry-server/` | Ingest contract + schema |
| Diagnostics hardware DB | `diagnostics-server/` | Import contract + schema |
| Signing keys / HMAC secrets | Secret manager / Plesk env | Never committed |
| WordPress bridge plugin (prod) | Private deploy artifact | Requirements doc only |
| Operator approval UI | `operator-dashboard/` | State machine contract only |

---

## 4. Import matrix

| From → To | Public module | Private module |
|-----------|---------------|----------------|
| **Public** | ✅ Allowed | ❌ **Forbidden** |
| **Private** | ✅ Contracts, shared version | ✅ Internal |
| **CI gate** | Blocks forbidden paths | Separate private CI |

Forbidden public imports include any path matching: `telemetry_server/`, `diagnostics_server/`, `cloudserver_private/`, `operator_dashboard/`, `licensing/`, `billing/`.

---

## 5. Data crossing the boundary

| Data type | Public repo | Private servers |
|-----------|-------------|-----------------|
| Telemetry envelope schema | ✅ Full schema | Implements validator |
| Redacted assessment blobs | ✅ Generator code | Stores ingest rows |
| User email / MFA state | ❌ Never | Registration DB only |
| Hardware fingerprints (hashed) | ✅ Contract fields | Diagnostics DB |
| Production API tokens | ❌ Never | Env / Plesk secrets |

Contracts define **shapes**; private repos define **persistence and policy enforcement**.

---

## 6. Documentation placeholders vs production

Docs and tests use example domains:

- `telemetry.internal.setuphelfer.example`
- `diagnose.internal.setuphelfer.example`
- `beta.internal.setuphelfer.example`

Production domains (`*.setuphelfer.de`) appear only in deployment plans as **targets**, never with embedded credentials.

---

## 7. Forbidden terms in public commits (excerpt)

Gate script rejects markers such as: `TELEMETRY_SERVER_SECRET`, `JWT_SECRET`, `PLESK_CATALOG_SUBMISSION_SECRET`, `LICENSE_ENFORCEMENT` (as implementation hooks). Use contract names instead.

---

## 8. Developer workflow

1. Define or update contract in public repo (+ JSON schema + pytest).  
2. Implement server in private repo against contract.  
3. Run public boundary gate before push (`exit 20` = manual review, no rename workaround).  
4. Deploy private services per `docs/deployment/*`; verify with Phase 0 only against **intended** environment.

---

## 9. Related documents

- `docs/architecture/PRIVATE_REPOSITORY_STRATEGY.md`  
- `docs/evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md`  
- `docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md`
