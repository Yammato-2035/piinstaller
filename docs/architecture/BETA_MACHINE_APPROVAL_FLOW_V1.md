# Beta Machine Approval Flow V1

**Version:** 1.0 · **Contract:** `backend/core/beta_machine_approval_contract_v1.py`

---

## 1. Purpose

Each physical machine running a beta Rescue Stick is identified by a **machine fingerprint** (derived from redacted hardware signals). Before telemetry enters the **accepted** path, an operator may need to approve the machine to prevent abuse and cloned sticks.

---

## 2. Approval statuses

| Status | Meaning |
|--------|---------|
| `unknown` | No BR/OP record yet |
| `pending` | Seen ingest or activation; awaiting review |
| `approved` | Cleared for `beta_server_accepted` telemetry |
| `blocked` | Ingest rejected |
| `revoked` | Previously approved, now denied |

Valid set: `APPROVAL_STATUSES` in contract.

---

## 3. State machine

```
                    ┌──────────┐
         ┌─────────►│ unknown  │
         │          └────┬─────┘
         │               │ first activation / ingest
         │               ▼
         │          ┌──────────┐
         │   ┌──────│ pending  │──────┐
         │   │      └────┬─────┘      │
         │   │ block     │ approve    │ auto (team batch)
         │   ▼           ▼            ▼
         │ ┌────────┐ ┌──────────┐
         └─┤ blocked│ │ approved │
           └────────┘ └────┬─────┘
                           │ revoke
                           ▼
                      ┌──────────┐
                      │ revoked  │
                      └──────────┘
```

`transition_approval(current, action)` supports:

- `approve`: `pending` or `unknown` → `approved`  
- `block`: any → `blocked`

---

## 4. Triggers into `pending`

| Event | Source |
|-------|--------|
| Type B activation completes | BR |
| First telemetry ingest with new fingerprint | TS → BR upsert |
| User adds second stick to same account | BR |
| Clone suspicion (duplicate stick_id, new fp) | BR heuristic → OP queue |

Team-provisioned batches may auto-approve when `team_batch_id` is in allowlist (private config).

---

## 5. Telemetry mode mapping

`telemetry_mode_for_machine(status, agreement_valid)`:

| Machine status | Agreement | Result mode |
|----------------|-----------|-------------|
| `approved` | valid | `beta_server_accepted` |
| `pending` | any | `restricted_local_only` |
| `blocked`, `revoked` | any | `quarantine` |
| other | — | `local_diagnostics_only` |

---

## 6. Operator workflow

1. OP dashboard lists `pending` machines with: fingerprint hash, stick_id, first_seen, last_assessment summary (redacted).  
2. Operator verifies legitimate beta participant.  
3. **Approve** → BR updates row, TS promotion job moves quarantined events.  
4. **Block** → TS returns `403` on subsequent ingests.

No PII (email) is required on OP hardware view — link via opaque `account_id` only.

---

## 7. API (internal, private)

| Method | Path | Action |
|--------|------|--------|
| GET | `/internal/v1/machines?status=pending` | List queue |
| POST | `/internal/v1/machines/{fp}/approve` | Approve |
| POST | `/internal/v1/machines/{fp}/block` | Block |

Public repo documents shapes only; implementation is private.

---

## 8. Validation

`validate_machine_entry(entry)` requires:

- `machine_fingerprint` non-empty  
- `approval_status` in allowed set  

Errors: `machine_fingerprint_required`, `invalid_approval_status`.

---

## 9. Audit and references

Transitions append to `machine_approval_audit` (operator ID, timestamp, reason). See `BETA_REGISTRATION_DB_SCHEMA_V1.md`, `BETA_DATA_FLOW_V1.md`.
