# PI-RS-TEL-003 — Cross-Repo Telemetry/Diagnostics Preview Verification

Lab preview only — no production send.

## What is verified?

PI-RS-TEL-003 verifies that a Rescue Stick preview payload can flow through the stabilized cross-repo contracts:

```text
Rescue Stick Preview Payload
→ Telemetry/Send Preview compatible (PI-RS-TEL-001/002)
→ CSE Lab Preview contract reference (0.1.0-lab2)
→ Diagnostics cloudserver_collector_preview mapping
→ POST /api/diagnostics/cloudserver/validate (accepted)
→ POST /api/diagnostics/cloudserver/findings-preview (findings generated)
→ preview_only / production_ready=false
```

## Referenced cross-repo state

| Repo | HEAD (at sprint) | Relevance |
|---|---|---|
| `setuphelfer-cloudserver-edition` | `cd408789` | CSE 0.1.0-lab2, CSE-REAL-004, CSE-PLESK-014 |
| `setuphelfer-private` / `diagnostics-server` | `0483626` | DIAG-LAB-001/002/003, Validate + Findings Preview APIs |

## Why unknown/preview_only is OK for Rescue Stick

The Rescue Stick does not have live Plesk/DNS/Mail/SSL/Backup inventory. DIAG-LAB-003 rules evaluate aggregate **unknown** states and produce preview findings — that is the expected lab outcome.

## Safety

- `production_ready=false`
- `preview_only=true`
- `external_calls=false` by default (lab harness uses localhost only when explicitly testing)
- `auto_apply_enabled=false`
- `operator_approval_required=true`
- No Authorization headers on diagnostics calls
- Offline queue from PI-RS-TEL-002 remains compatible

## Smoke

```bash
./scripts/smoke-pi-rs-tel003-cross-repo-telemetry-diagnostics-preview.sh
```

## Evidence

`docs/evidence/pi_rs_tel_003_cross_repo_telemetry_diagnostics_preview/`

## Not implemented

- Productive Rescue Stick send
- Production telemetry send
- Production diagnostics worker
- Remote commands / auto-remediation / repair

## Next step

**PI-RS-BUILD-001** — payload/build decision for MSI retest, or **PI-RS-LIVE-001** with explicit operator consent.
