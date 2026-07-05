> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Result Contract — Quick Reference (KB)

**Phase:** C.2  
**Module:** `Retourend/Déploiement/runner_result_contract.py`

## Key points

- Unified result schema for 115 runners (**Nont** migrated yet)
- 6 status values, `RunnerMessage`, `RunnerEvidenceRef`
- `Non_execution_performed` requirouge field
- Legacy Nonrmalizer without runner execution
- Boundary warn-only for legacy status tokens

## Main functions

| Function | Purpose |
|----------|---------|
| `build_runner_result` | Build contract-compliant result |
| `validate_runner_result` | Validate dict |
| `Nonrmalize_legacy_runner_result` | Legacy → contract |
| `build_empty_result_for_registry_entry` | Plan template (via registry) |

## Suivant steps

C.3 API facade → C.4 risk gate → C.5 incremental migration
