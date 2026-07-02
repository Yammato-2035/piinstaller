# Diagnostics Server Hardware DB Beta 0.1

**Version:** beta.0.1 · **Mock:** `backend/dev/diagnostics_mock_server_v1.py` (port 8102)  
**JSON schema:** `hardware_db_schema_v1.json`, `diagnostics_learning_import_contract_v1.schema.json`

---

## 1. Purpose

The diagnostics server maintains a **hardware knowledge base** built from redacted telemetry assessments. It correlates machine classes (CPU, chipset, storage, network adapters) with rescue outcomes to improve recommendations — without storing PII or raw serial numbers.

---

## 2. Planes (DS.1 subset)

| Plane | Beta.0.1 scope |
|-------|----------------|
| Ingest | `POST /v1/learning/import` only |
| Session | Deferred |
| Analysis | Rule stubs + manual review queue |
| Knowledge | Hardware profiles + observation links |

Full target architecture: `DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md`.

---

## 3. Learning import flow

```
Telemetry Server ──► POST /v1/learning/import
                         │
                         ├─ JSON schema validate
                         ├─ PII walker (reject email, ip, mac, …)
                         ├─ hardware_key derivation
                         └─ insert hardware_observations (review_required=true)
```

Mock response:

```json
{
  "import_status": "accepted",
  "review_required": true,
  "hardware_key": "hw_…"
}
```

PII detected → `422 rejected_pii`.

---

## 4. Hardware key

Derived from normalized, redacted assessment fields:

- CPU model family (not serial)  
- Mainboard vendor/product codes  
- Storage bus type + capacity bucket  
- GPU class (if present)  
- Firmware flags (UEFI/Legacy)

Algorithm is private; public contract exposes only `hardware_key` string.

---

## 5. Core tables (summary)

See `sql/diagnostics_hardware_db_schema_v1.sql` and `TELEMETRY_SERVER_DB_SCHEMA_V1.md` for cross-links.

| Table | Role |
|-------|------|
| `hardware_profiles` | Stable key → trait vector |
| `hardware_observations` | Per-event snapshot + outcome tags |
| `hardware_review_queue` | Operator sign-off |
| `learning_import_audit` | Import attempts |

---

## 6. Review policy

All beta imports land with `review_required=true` until operator confirms:

- No accidental PII leakage  
- Hardware key clustering is sane  
- No duplicate spam from broken stick loop

Approved observations feed FAQ/KB candidates (manual export in beta.0.1).

---

## 7. Forbidden data

Reject payload if any key matches (case-insensitive): `email`, `phone`, `ip`, `mac`, `account_id`.

Also reject nested values under `FORBIDDEN_ID_DOCUMENT_FIELDS` from agreement gate.

---

## 8. API surface (beta.0.1)

| Method | Path | Caller |
|--------|------|--------|
| GET | `/health` | Monitor |
| POST | `/v1/learning/import` | Telemetry Server |

No public read API in beta.0.1.

---

## 9. Deployment

Target: `diagnose.setuphelfer.de` — `DIAGNOSTICS_SERVER_IONOS_PLESK_DEPLOYMENT_PLAN_V1.md`.

---

## 10. Related documents

- `hardware_db_schema_v1.json`  
- `diagnostics_learning_import_contract_v1.schema.json`  
- `BETA_DATA_FLOW_V1.md`
