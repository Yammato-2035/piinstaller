# Service Interaction Matrix V1

**Version:** 1.0 · **Scope:** Beta.0.1 cloud stack + Rescue Stick clients  
**Rule:** If a cell is not marked ✅, the interaction is **forbidden** unless explicitly approved in a security review.

---

## 1. Actors

| ID | Actor | Description |
|----|-------|-------------|
| RS | Rescue Stick (live) | Booted diagnostics medium |
| SH | Setuphelfer local | `/opt/setuphelfer` on installed system |
| BR | Beta Registration Server | Accounts, sticks, agreements |
| TS | Telemetry Server | Ingest + quarantine |
| DS | Diagnostics Server | Hardware DB + learning |
| WP | WordPress (marketing) | Landing + CTA links |
| OP | Operator Dashboard | Machine approval (private) |
| LAB | Dev mock stack | Ports 8100–8102 |

---

## 2. Interaction matrix (allowed channels)

Legend: ✅ Allowed · ⚠️ Restricted · ❌ Forbidden · — Not applicable

### 2.1 Outbound from clients

| From ↓ / To → | BR | TS | DS | SH | OP | WP |
|---------------|----|----|----|----|----|-----|
| **RS** | ⚠️ register/attest only | ✅ ingest/dry-run | ❌ | ❌ | ❌ | ❌ |
| **SH** | ❌ (beta via browser) | ⚠️ product telemetry (future) | ❌ | — | ❌ | ❌ |
| **WP** | ✅ HTTPS redirect/API | ❌ | ❌ | ❌ | ❌ | — |
| **TS** | ⚠️ permission check | — | ✅ learning forward | ❌ | ⚠️ status webhook | ❌ |
| **DS** | ❌ | ❌ | — | ❌ | ⚠️ review queue | ❌ |
| **OP** | ✅ approve machine | ⚠️ read ingest meta | ✅ read hardware | ❌ | — | ❌ |
| **LAB** | ✅ mock | ✅ mock | ✅ mock | ⚠️ dev only | ❌ | ❌ |

### 2.2 Inbound to servers (who may call)

| Server | Allowed callers | Endpoints (examples) |
|--------|-----------------|----------------------|
| **BR** | Browser (public), WP bridge, TS (internal) | `/public/v1/beta/*`, `/internal/v1/sticks/*` |
| **TS** | RS, LAB | `/v1/telemetry/ingest`, `/dry-run`, `/health` |
| **DS** | TS (service token), OP | `/v1/learning/import`, `/health` |
| **OP** | Operator browser (VPN/MFA) | `/internal/v1/machines/*` |

---

## 3. Forbidden interactions (explicit)

| # | Interaction | Reason |
|---|-------------|--------|
| F-01 | TS → RS (any callback) | No remote command plane |
| F-02 | DS → RS | No pull/fix channel |
| F-03 | RS → DS direct | Must pass through TS quarantine gate |
| F-04 | WP → TS/DS | Marketing host must not hold ingest tokens |
| F-05 | Public internet → OP without MFA/VPN | Operator surface is private |
| F-06 | TS execute/shell/fix routes | Matches `FORBIDDEN_PATH_PREFIXES` in mock |
| F-07 | BR storing full telemetry payloads | Registration DB is identity-light |
| F-08 | DS auto-merging quarantine rows | Requires `accepted` ingest status |

---

## 4. Authentication mechanisms

| Link | Mechanism |
|------|-----------|
| RS → TS | Stick `device_public_key_id` + HMAC/signature over canonical body |
| RS → BR | User session + CSRF (browser); stick token for Type B activation |
| TS → BR | Internal service token, `check-upload-permission` |
| TS → DS | mTLS or bearer token (deploy-specific), scoped to `learning/import` |
| OP → BR/DS | Operator JWT, IP allowlist |

Secrets are **never** stored in the public repository.

---

## 5. Data classes per link

| Link | Payload | PII allowed |
|------|---------|-------------|
| RS → TS | `telemetry.rescue.beta.v2` | No (privacy flags false) |
| TS → DS | `diagnostics_learning_import_contract_v1` | No — rejected at DS |
| Browser → BR | Registration form | Email only (+ MFA), no ID documents |
| TS → BR | Permission check metadata | Stick ID hash, agreement flags |

---

## 6. Failure isolation

- TS unreachable: RS spools to USB (`rescue_telemetry_queue_v1`), retries with backoff.  
- BR unreachable: Stick operates local-only; upload mode stays `restricted_local_only`.  
- DS unreachable: TS accepts ingest but sets `diagnostics_forwarded: false`.  
- OP unreachable: Machine stays `pending`; telemetry may quarantine per policy.

---

## 7. Mock parity

Lab mocks on 8100–8102 must implement the same **forbidden route** behavior as production TS to keep CI honest.

---

## 8. Related documents

- `BETA_DATA_FLOW_V1.md`  
- `SETUPHELFER_BETA_SYSTEM_ARCHITECTURE_V1.md`  
- `RESCUE_TELEMETRY_CLIENT_CONTRACT_V2.md`
