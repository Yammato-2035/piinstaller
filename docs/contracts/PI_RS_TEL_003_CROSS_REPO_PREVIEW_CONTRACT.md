# PI-RS-TEL-003 — Cross-Repo Preview Contract

Preview only. `production_ready=false` always.

## Purpose

Define how the Rescue Stick produces a **preview payload** compatible with:

- CSE **0.1.0-lab2** (CSE-REAL-004 / CSE-PLESK-014 / CSE-VERSION-SYNC-002)
- Diagnostics **DIAG-LAB-003** (`0483626`+ on `setuphelfer-private` main)

## Rescue Stick Preview Payload

| Field | Requirement |
|---|---|
| `source_kind` | `rescue_stick` |
| `event_kind` | `rescue_stick_cross_repo_preview` |
| `diagnostics_aggregates` | unknown/preview_only subsections for Plesk/DNS/Mail/SSL/Backup |
| `cross_repo.cse_target_compatibility` | `0.1.0-lab2` |
| `cross_repo.diagnostics_contract_reference` | `DIAG-LAB-003` |
| `cross_repo.preview_only` | `true` |
| `cross_repo.external_calls` | `false` (default) |
| `cross_repo.production_ready` | `false` |
| `cross_repo.auto_apply_enabled` | `false` |
| `cross_repo.operator_approval_required` | `true` |

## Diagnostics Mapping

Rescue payload maps to `cloudserver_collector_preview` for:

- `POST /api/diagnostics/cloudserver/validate`
- `POST /api/diagnostics/cloudserver/findings-preview`

Missing server inventory is expressed as `unknown` / `preview_only` — not an error.

## Safety

- No raw logs
- No secrets, tokens, authorization headers, private keys
- No real customer domains (fixtures use `example.invalid` / `lab.example.invalid`)
- No remote commands
- No auto-remediation
- Offline queue preview remains compatible (PI-RS-TEL-002)

## Verification Scope

Cross-repo verification is **localhost diagnostics subprocess only** during lab tests.

## Not In Scope

- Production Rescue Stick send
- Production telemetry send
- Production diagnostics worker
- Live server repair
