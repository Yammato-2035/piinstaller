# Remote Lab Job Contract

Target-bound job model for `ASUS_ROG_GABRIEL_LAB`. Extends existing `rescue_remote` concepts; does not create a second remote platform.

## Job shape

```json
{
  "schema_version": "1",
  "job_id": "labjob-…",
  "run_id": "asus-win11-…",
  "target_profile": "ASUS_ROG_GABRIEL_LAB",
  "target_fingerprint": "<machine_id>",
  "action_type": "shell|disk|restore|efi|secure_boot|firmware|diagnostic",
  "command": null,
  "parameters": {},
  "risk_class": "read_only|controlled|destructive|firmware",
  "bitlocker_mutation": false,
  "created_at": "…Z",
  "expires_at": "…Z",
  "nonce": "…",
  "requested_by": "…",
  "authorization_profile_hash": "…",
  "signature": "…",
  "command_hash": "…",
  "state": "created"
}
```

## Validation

- Wrong `target_profile` → blocked
- Expired `expires_at` → blocked
- Nonce replay → blocked
- Invalid HMAC signature → blocked
- Identity not `exact_match` → blocked
- Fingerprint ≠ observed `machine_id` → blocked
- Shell command matching BitLocker mutation patterns → blocked
- `bitlocker_mutation: true` → schema/runtime reject

## States

`created` → `validated` → `identity_confirmed` → `preflight` → `running` → (`waiting_for_reboot` → `reconnected`) → `verifying` → `success` | `failed` | `blocked` | `cancelled`

After reboot, resume by `job_id` + `run_id` (store: `rescue_lab_job_store`).

## Shell audit (ASUS profile only)

Unrestricted Linux commands are allowed **only** for this profile after identity confirmation. Every command records timestamp, hash, stdout/stderr, exit code. No interactive unlogged session. No auto-chaining of follow-up commands from stdout. Secrets (BitLocker keys) are redacted.

## APIs

- `POST /api/lab/jobs/plan`
- `POST /api/lab/jobs`
- `GET /api/lab/jobs/{job_id}`
- `POST /api/lab/jobs/{job_id}/cancel`
- `POST /api/lab/jobs/{job_id}/validate`

Agent pull/execute remains bridged to existing `/api/rescue-remote/*` where present; lab contract is the authorization envelope.
