# KB: DEPLOY_RUNNER_LIFECYCLE

## Überblick

State-Machine für den Deploy-Write-Runner mit **Lockfiles**, **TOCTOU-Rechecks** (read-only) und **JSON-Lines-Audit**. Aktuelle Phase: Dry-run endet in `completed` ohne `writing`/`verifying` auf echten Geräten.

## Kern-API

| Funktion | Rolle |
|----------|--------|
| `build_runner_lifecycle` | Startobjekt `created` |
| `transition_runner_state` | Legale Übergänge, fail-closed |
| `acquire_runner_lock` / `release_runner_lock` | Exklusives Lock pro `job_id` |
| `extract_runner_baseline_from_job` | Snapshot für Drift-Vergleich |
| `recheck_runner_consistency` | Checkpoint `pre_ready` / `pre_writing` / `pre_verifying` |
| `append_runner_audit` | Eine Zeile JSON pro Ereignis |
| `cleanup_stale_runner_locks` | Tote/abgelaufene Locks |
| `cleanup_expired_runner_jobs` | Job-JSON mit abgelaufenem `expires_at` |
| `prepare_audit_rotation` | Alte `audit-*.jsonl` löschen |

## Dry-run

`deploy_write_runner.dry_run_with_loaded_job` führt Lifecycle + drei TOCTOU-Checks + Audit aus; Lock wird im `finally` freigegeben.

## Verwandt

- `docs/deploy/DEPLOY_RUNNER_LIFECYCLE_DE.md` / `_EN.md`
- `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_DE.md`
- `docs/evidence/DEPLOY_RUNNER_LIFECYCLE_RUNTIME.md`
