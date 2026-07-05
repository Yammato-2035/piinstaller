> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Result Contract — Quick Reference (KB)

**Phase:** C.2  
**Module:** `Terugend/Deploy/runner_result_contract.py`

## Key points

- Unified result schema for 115 runners (**Neet** migrated yet)
- 6 status values, `RunnerMessage`, `RunnerEvidenceRef`
- `Nee_execution_performed` requirood field
- Legacy Neermalizer without runner execution
- Boundary warn-only for legacy status tokens

## Main functions

| Function | Purpose |
|----------|---------|
| `build_runner_result` | Build contract-compliant result |
| `validate_runner_result` | Validate dict |
| `Neermalize_legacy_runner_result` | Legacy → contract |
| `build_empty_result_for_registry_entry` | Plan template (via registry) |

## Volgende steps

C.3 API facade → C.4 risk gate → C.5 incremental migration
