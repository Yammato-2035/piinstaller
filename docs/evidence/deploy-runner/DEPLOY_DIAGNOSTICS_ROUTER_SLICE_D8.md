# Deploy Diagnostics Router Slice (Phase D.8)

## Gewählte Routen (6 POST)

| Route | runner_id | Response-Key |
|---|---|---|
| `/runner/manual-runtime/failure-injection-matrix` | `runner_manual_runtime_failure_injection_matrix` | `matrix` |
| `/runner/manual-runtime/failure-execution-preview` | `runner_manual_runtime_failure_execution_preview` | `preview` |
| `/runner/manual-runtime/failure-operator-checklists` | `runner_manual_runtime_failure_operator_checklists` | `checklists` |
| `/runner/manual-runtime/failure-test-sessions` | `runner_manual_runtime_failure_test_sessions` | `sessions` |
| `/runner/manual-runtime/failure-readiness-gate` | `runner_manual_runtime_failure_readiness_gate` | `readiness` |
| `/runtime-identifier-zero-state-verification` | `runner_runtime_identifier_zero_state_verification` | `runtime_identifier_zero_state_verification` |

Alle mit `decoupling_phase="d8"`, `facade_decoupling_d8: true`, `allowed_to_execute: false`.

## Ausgeschlossen

- `/runner/audit/*` — Helper-Funktionen ohne sauberes Facade-Mapping
- Test-Plan-Routen — `blocked_operator_required`
- Rescue-Validierungen — Rescue-Domain
- Execute/Write/Apply-Pfade

## Verbleibend in routes.py

Audit-, Sandbox-, Lab-Readiness-, Precheck- und Rescue-Diagnostics-Routen unverändert.
