# Beta Stick Activation Flow — Type B (Registered ISO)

**Version:** 1.0 · **Stick type:** `registered_iso`  
**Related:** `BETA_STICK_REGISTRATION_AND_ATTESTATION_V1.md`

---

## 1. Summary

Type B activation pairs a **user-registered beta account** with a **self-flashed Rescue ISO**. The stick cannot upload telemetry until activation completes and machine approval reaches `approved`.

---

## 2. Preconditions

| Requirement | Checked by |
|-------------|------------|
| Beta account created | BR |
| Email verified | BR |
| MFA enabled | BR |
| Beta agreement accepted (`agreement_status: valid`) | BR |
| ISO downloaded from authorized URL | CDN + BR token |
| USB ≥ 16 GB, backup of existing data | User |

---

## 3. Activation sequence

1. User logs in (MFA) → requests activation token from BR.  
2. User flashes authorized ISO (hash verified).  
3. Rescue boots → local activation UI.  
4. `POST /public/v1/sticks/activate` with `activation_token`, `machine_fingerprint`.  
5. BR enrolls stick + key; stick writes local registry.  
6. First telemetry → TS (quarantine until machine `approved`).

---

## 4. Activation API (public surface)

**POST** `/public/v1/sticks/activate`

Request (example shape):

```json
{
  "activation_token": "tok_…",
  "machine_fingerprint": "fp_…",
  "iso_build_id": "iso_…",
  "client_nonce": "…"
}
```

Response:

```json
{
  "stick_id": "stick_…",
  "stick_type": "registered_iso",
  "device_public_key_id": "key_…",
  "attestation_mode": "signature",
  "machine_approval_status": "pending"
}
```

Errors: `invalid_token`, `iso_mismatch`, `account_not_ready`, `mfa_required`.

---

## 5. Local persistence after activation

| Path | Content |
|------|---------|
| `beta/stick_registry.json` | Stick ID, key handles (not private key in plaintext on FAT) |
| `evidence/activation/` | Activation audit log (no PII) |

If activation file is missing on subsequent boots, UI shows **re-activate** flow; old `stick_id` remains in BR unless revoked.

---

## 6. Post-activation gates

| Gate | Upload mode |
|------|-------------|
| Activation OK, machine `pending` | `beta_server_quarantine` |
| Machine `approved` + agreement valid | `beta_server_accepted` |
| Agreement missing | quarantine 14d retention |
| Activation never completed | `restricted_local_only` |

---

## 7. Failure handling

- **Token expired:** User generates new token in portal (old token invalidated).  
- **Wrong ISO:** Hash mismatch → block activation, log `iso_mismatch`.  
- **Offline activation:** Not supported in v1; stick stays local-only until online.  
- **Cloned USB:** Second fingerprint with same stick_id → BR flags review, machine `blocked` until OP resolves.

---

## 8. Security and references

Activation token: single-use, 15-minute TTL. Private key generated on stick; BR stores only `device_public_key_id` fingerprint. See `BETA_MACHINE_APPROVAL_FLOW_V1.md`, `beta_stick_registry.schema.json`.
