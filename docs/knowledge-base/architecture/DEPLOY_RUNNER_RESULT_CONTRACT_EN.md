# Deploy Runner Result Contract — Quick Reference (KB)

**Phase:** C.2  
**Module:** `backend/deploy/runner_result_contract.py`

## Key points

- Unified result schema for 115 runners (**not** migrated yet)
- 6 status values, `RunnerMessage`, `RunnerEvidenceRef`
- `no_execution_performed` required field
- Legacy normalizer without runner execution
- Boundary warn-only for legacy status tokens

## Main functions

| Function | Purpose |
|----------|---------|
| `build_runner_result` | Build contract-compliant result |
| `validate_runner_result` | Validate dict |
| `normalize_legacy_runner_result` | Legacy → contract |
| `build_empty_result_for_registry_entry` | Plan template (via registry) |

## Next steps

C.3 API facade → C.4 risk gate → C.5 incremental migration
