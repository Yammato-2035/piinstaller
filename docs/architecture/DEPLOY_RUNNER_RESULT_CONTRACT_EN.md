# Deploy Runner Result Contract (Phase C.2)

**Module:** `backend/deploy/runner_result_contract.py`  
**Contract version:** `CONTRACT_VERSION = 1`  
**Prerequisite:** C.1 registry (`runner_registry.py`)

## Why a result contract?

115 deploy runners today emit **14+** different status literals and inconsistent dict shapes (`errors`, `evidence_files`, nested `file_results`). Dashboard, DCC, and future automation cannot aggregate outcomes reliably.

C.2 defines a **unified result schema** — without executing or migrating runners.

## Status values (`RunnerResultStatus`)

| Status | Meaning |
|--------|---------|
| `ok` | Success / gate passed |
| `review_required` | Manual review needed |
| `blocked` | Hard blocked (with `errors`) |
| `failed` | Failed (with `errors`) |
| `skipped` | Intentionally skipped |
| `not_applicable` | Not applicable |

`unknown` is allowed only as `kind`, **not** as `status`.

## Error and warning structure

`RunnerMessage`: `{ code, message, severity }` with `RunnerResultSeverity` (`info`, `warning`, `error`, `critical`).

Rules:

- `blocked` / `failed` → at least one `errors` entry
- `review_required` → at least `warnings` or `errors`
- No secrets in `metadata` (keys like `password`, `token`)

## Evidence paths

`RunnerEvidenceRef`: `{ path, read_only?, label? }`

- Workspace-relative paths preferred (`docs/evidence/...`)
- Absolute paths only with `read_only: true`
- Forbidden: `.env`, `/etc/shadow`, credential paths

## `no_execution_performed`

Required field (`bool`). `true` for plan/template/static analysis only — separates C.2 preparation from real runtime execution (C.4 risk gate).

## Link to C.1 registry

- `build_empty_result_for_registry_entry(entry)` — plan template per runner
- `validate_registry_result_contract(entry, result)` — contract + registry alignment
- inherit `risk_level` / `execution_policy` from registry entry

## Preparation for C.3 / C.4

| Phase | Use |
|-------|-----|
| **C.3 API facade** | **complete** — `get_runner_empty_result()` returns `RunnerResult.to_dict()` |
| **C.4 Risk gate** | Policy + `no_execution_performed` before execution |
| **C.5 migration** | `normalize_legacy_runner_result()` per runner incrementally |

## API

- `build_runner_result(...)`
- `validate_runner_result(dict) -> RunnerResultValidation`
- `normalize_legacy_runner_result(runner_id, raw, registry_entry?)`
- `summarize_runner_results(list)`

## Tests

`backend/tests/test_deploy_runner_result_contract_v1.py`

## References

- DE: `DEPLOY_RUNNER_RESULT_CONTRACT.md`
- Pattern audit: `docs/evidence/deploy-runner/RUNNER_RESULT_PATTERN_AUDIT_C2.md`
- Registry: `DEPLOY_RUNNER_REGISTRY_EN.md`
