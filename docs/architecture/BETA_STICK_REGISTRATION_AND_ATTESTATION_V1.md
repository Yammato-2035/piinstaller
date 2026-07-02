# Beta Stick Registration and Attestation V1

**Version:** 1.0 · **Registry schema:** `beta_stick_registry.schema.json`

---

## 1. Two stick origins

Beta supports two production stick types (plus lab `mock`):

| Type | `stick_type` | Provisioning model |
|------|--------------|-------------------|
| **Type A — Team provisioned** | `team_provisioned` | Operator pre-registers stick in BR before USB shipment |
| **Type B — Registered ISO** | `registered_iso` | User downloads ISO, activates via portal (see `beta_stick_activation_flow.md`) |

Both must present a valid `device_public_key_id` and pass attestation before telemetry leaves quarantine.

---

## 2. Type A: Team provisioned flow

```
Operator (OP) ──► BR: create stick record
       │
       ├── stick_id assigned
       ├── team batch ID logged
       └── public key enrolled (HMAC or signature key id)

Manufacturing ──► write stick manifest to USB SETUP partition
       │
Rescue boot ──► read manifest ──► attest ──► TS ingest
```

**Attestation modes:**

- `hmac` — shared secret derived per stick at provision time (stored only on stick + BR).  
- `signature` — stick holds private key; BR holds public key fingerprint.

Team sticks may ship before end-user beta account exists; first boot links `machine_fingerprint` to pending approval.

---

## 3. Type B: Registered ISO flow

```
User ──► WP landing ──► BR signup + MFA
     ──► download signed ISO
     ──► activation wizard (Type B)
     ──► BR issues stick token + key enrollment
     ──► stick writes local registry JSON
```

ISO hash and download URL are tied to `registry_entry.iso_build_id`. Re-registration of same USB serial is idempotent.

---

## 4. Registry entry (logical)

See `beta_stick_registry.schema.json` for full JSON Schema. Core fields:

| Field | Description |
|-------|-------------|
| `stick_id` | Stable identifier |
| `stick_type` | `team_provisioned` \| `registered_iso` |
| `status` | `provisioned`, `active`, `revoked`, `expired` |
| `device_public_key_id` | Key reference for verify |
| `attestation_mode` | `hmac` \| `signature` |
| `created_at` / `revoked_at` | Audit |
| `team_batch_id` | Type A only |
| `account_id` | Type B link (opaque UUID, not email) |
| `iso_build_id` | Type B only |

---

## 5. Attestation verification (telemetry server)

On ingest:

1. Resolve `stick_id` in registry (BR cache or TS replica).  
2. Load public key / HMAC material by `device_public_key_id`.  
3. Verify signature over canonical JSON (whitespace-normalized).  
4. Reject revoked sticks with `403 rejected_auth`.

Mock sticks use `attestation_mode: mock` — **lab only**.

---

## 6. Revocation

| Action | Effect |
|--------|--------|
| Operator revoke | `status=revoked`, ingest denied |
| Key rotation | New `device_public_key_id`, grace window 7d |
| ISO superseded | Old `iso_build_id` downloads disabled |

Revoked sticks may still boot locally; telemetry upload mode becomes `disabled`.

---

## 7. Prohibitions

- No plaintext storage of HMAC secrets in BR database (use KMS/hash).  
- No binding stick to national ID fields (`beta_agreement_gate_v1` forbidden list).  
- Public repo contains **schema only**, not production registry exports.

---

## 8. Mock / CI

Test fixtures use `stick_type: mock` and port 8100 BR mock for permission checks.

---

## 9. Related documents

- `beta_stick_activation_flow.md`  
- `BETA_REGISTRATION_DB_SCHEMA_V1.md`  
- `beta_stick_registry.schema.json`
