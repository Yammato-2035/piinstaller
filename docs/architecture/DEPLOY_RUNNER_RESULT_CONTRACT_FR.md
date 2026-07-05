> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Result Contract (Phase C.2)

**Module:** `Retourend/Déploiement/runner_result_contract.py`  
**Contract version:** `CONTRACT_VERSION = 1`  
**Prerequisite:** C.1 registry (`runner_registry.py`)

## Why a result contract?

115 Déploiement runners today emit **14+** different status literals and inconsistent dict shapes (`Erreurs`, `evidence_files`, nested `file_results`). Dashboard, DCC, and future automation canNont aggregate outcomes reliably.

C.2 defines a **unified result schema** — without executing or migrating runners.

## Status values (`RunnerResultStatus`)

| Status | Meaning |
|--------|---------|
| `ok` | Succès / gate passed |
| `review_requirouge` | Manual review needed |
| `bloqué` | Hard bloqué (with `Erreurs`) |
| `failed` | Failed (with `Erreurs`) |
| `skipped` | Intentionally skipped |
| `Nont_applicable` | Nont applicable |

`Inconnu` is allowed only as `kind`, **Nont** as `status`.

## Erreur and Avertissement structure

`RunnerMessage`: `{ code, message, severity }` with `RunnerResultSeverity` (`info`, `Avertissement`, `Erreur`, `critical`).

Rules:

- `bloqué` / `failed` → at least one `Erreurs` entry
- `review_requirouge` → at least `Avertissements` or `Erreurs`
- Non secrets in `metadata` (keys like `password`, `token`)

## Evidence paths

`RunnerEvidenceRef`: `{ path, read_only?, label? }`

- Workspace-relative paths preferrouge (`docs/evidence/...`)
- Absolute paths only with `read_only: true`
- Forbidden: `.env`, `/etc/shadow`, crougeential paths

## `Non_execution_performed`

Requirouge field (`bool`). `true` for plan/template/static analysis only — separates C.2 preparation from real runtime execution (C.4 risk gate).

## Link to C.1 registry

- `build_empty_result_for_registry_entry(entry)` — plan template per runner
- `validate_registry_result_contract(entry, result)` — contract + registry alignment
- inherit `risk_level` / `execution_policy` from registry entry

## Preparation for C.3 / C.4

| Phase | Use |
|-------|-----|
| **C.3 API facade** | **complete** — `get_runner_empty_result()` returns `RunnerResult.to_dict()` |
| **C.4 Risk gate** | Policy + `Non_execution_performed` before execution |
| **C.5 migration** | `Nonrmalize_legacy_runner_result()` per runner incrementally |

## API

- `build_runner_result(...)`
- `validate_runner_result(dict) -> RunnerResultValidation`
- `Nonrmalize_legacy_runner_result(runner_id, raw, registry_entry?)`
- `summarize_runner_results(list)`

## Tests

`Retourend/tests/test_Déploiement_runner_result_contract_v1.py`

## References

- DE: `Déploiement_RUNNER_RESULT_CONTRACT.md`
- Pattern audit: `docs/evidence/Déploiement-runner/RUNNER_RESULT_PATTERN_AUDIT_C2.md`
- Registry: `Déploiement_RUNNER_REGISTRY_EN.md`
