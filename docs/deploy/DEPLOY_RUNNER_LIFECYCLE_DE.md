# Deploy Runner — Lifecycle (Dry-run)

## Zweck

Zustandsmaschine, Locking, read-only TOCTOU-Rechecks und Audit für den **Real-Write-Runner**. **Kein** Blockdevice-Write, kein `dd`/`mkfs`/`mount`, keine sudoers-Installation in dieser Phase.

## Zustände

`created` → `validated` → `locked` → `ready` → (`writing` → `verifying` →) `completed`

Terminal: `completed`, `aborted`, `failed`, `expired` — keine weiteren Übergänge.

Spätere Phasen nutzen `writing` / `verifying`; der **Dry-run** springt von `ready` nach `completed`.

## API-Codes

- `DEPLOY_RUNNER_STATE_CREATED` — erfolgreicher Aufbau via `build_runner_lifecycle`
- `DEPLOY_RUNNER_STATE_INVALID` — ungültige Eingabe
- `DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED` — verbotener Übergang
- `DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK` — Übergang erlaubt (Erfolg)

## Locking

- Verzeichnis: `backend/cache/deploy/runner-locks/`
- Exklusive Datei via `O_CREAT|O_EXCL` (kein `flock`-Subprozess)
- JSON: `lock_id`, `job_id`, `pid`, `created_at`, `state`
- Stale: tote PID oder Alter &gt; TTL (Standard 3600 s)
- `cleanup_stale_runner_locks` / `cleanup_expired_runner_locks`

## TOCTOU-Minimierung

`extract_runner_baseline_from_job` + `recheck_runner_consistency` an Checkpoints:

- `pre_ready` (vor `ready`)
- `pre_writing` (vor würde-write)
- `pre_verifying` (vor Verify)

Verglichen werden u. a. `job_hash`, `snapshot_fingerprint`, `image_sha256`, `image_size_bytes`, `target_device`, `mounted`, `removable`, `readonly`, `guard_subset`. Runtime-Metadaten können im Job-Dict als `_runtime_mounted` / `_runtime_removable` / `_runtime_readonly` gesetzt werden (nur für Tests/Integration).

## Audit

- `backend/cache/deploy/runner-audit/audit-YYYYMMDD.jsonl`
- Keine vollständigen Checksummen, keine Tokens/SSH-Keys
- `prepare_audit_rotation(keep_days=…)` für Altdaten

## Cleanup

- `cleanup_expired_runner_jobs`: Job-JSON im angegebenen Root mit abgelaufenem `expires_at`
- Locks: siehe oben

## Dry-run CLI

`backend/tools/deploy_write_runner.py --job … --dry-run` — erweiterte JSON-Antwort u. a. mit `runner_state`, `lock_id`, `audit_entries_written`.

## Module

- `backend/deploy/runner_lifecycle.py`
- `backend/tools/deploy_write_runner.py`

## Tests

`backend/tests/test_deploy_runner_lifecycle_v1.py`

## Evidence

`docs/evidence/DEPLOY_RUNNER_LIFECYCLE_RUNTIME.md`
