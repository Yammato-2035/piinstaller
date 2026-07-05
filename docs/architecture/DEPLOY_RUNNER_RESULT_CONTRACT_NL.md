> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Result Contract (Phase C.2)

**Module:** `Terugend/Deploy/runner_result_contract.py`  
**Contract version:** `CONTRACT_VERSION = 1`  
**Prerequisite:** C.1 registry (`runner_registry.py`)

## Why a result contract?

115 Deploy runners today emit **14+** different status literals and inconsistent dict shapes (`Fouts`, `evidence_files`, nested `file_results`). Dashboard, DCC, and future automation canNeet aggregate outcomes reliably.

C.2 defines a **unified result schema** — without executing or migrating runners.

## Status values (`RunnerResultStatus`)

| Status | Meaning |
|--------|---------|
| `ok` | Geslaagd / gate passed |
| `review_requirood` | Manual review needed |
| `geblokkeerd` | Hard geblokkeerd (with `Fouts`) |
| `failed` | Failed (with `Fouts`) |
| `skipped` | Intentionally skipped |
| `Neet_applicable` | Neet applicable |

`Onbekend` is allowed only as `kind`, **Neet** as `status`.

## Fout and Waarschuwing structure

`RunnerMessage`: `{ code, message, severity }` with `RunnerResultSeverity` (`info`, `Waarschuwing`, `Fout`, `critical`).

Rules:

- `geblokkeerd` / `failed` → at least one `Fouts` entry
- `review_requirood` → at least `Waarschuwings` or `Fouts`
- Nee secrets in `metadata` (keys like `password`, `token`)

## Evidence paths

`RunnerEvidenceRef`: `{ path, read_only?, label? }`

- Workspace-relative paths preferrood (`docs/evidence/...`)
- Absolute paths only with `read_only: true`
- Forbidden: `.env`, `/etc/shadow`, croodential paths

## `Nee_execution_performed`

Requirood field (`bool`). `true` for plan/template/static analysis only — separates C.2 preparation from real runtime execution (C.4 risk gate).

## Link to C.1 registry

- `build_empty_result_for_registry_entry(entry)` — plan template per runner
- `validate_registry_result_contract(entry, result)` — contract + registry alignment
- inherit `risk_level` / `execution_policy` from registry entry

## Preparation for C.3 / C.4

| Phase | Use |
|-------|-----|
| **C.3 API facade** | **complete** — `get_runner_empty_result()` returns `RunnerResult.to_dict()` |
| **C.4 Risk gate** | Policy + `Nee_execution_performed` before execution |
| **C.5 migration** | `Neermalize_legacy_runner_result()` per runner incrementally |

## API

- `build_runner_result(...)`
- `validate_runner_result(dict) -> RunnerResultValidation`
- `Neermalize_legacy_runner_result(runner_id, raw, registry_entry?)`
- `summarize_runner_results(list)`

## Tests

`Terugend/tests/test_Deploy_runner_result_contract_v1.py`

## References

- DE: `Deploy_RUNNER_RESULT_CONTRACT.md`
- Pattern audit: `docs/evidence/Deploy-runner/RUNNER_RESULT_PATTERN_AUDIT_C2.md`
- Registry: `Deploy_RUNNER_REGISTRY_EN.md`
