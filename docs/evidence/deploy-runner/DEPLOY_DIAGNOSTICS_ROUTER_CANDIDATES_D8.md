# Deploy Diagnostics Router Candidates (Phase D.8)

**HEAD:** 59420b4 (vor D.8)

## Kandidaten-Tabelle

| Route | runner_id | risk_level | execution_policy | C.4 Decision | decoupled | D.8 geeignet | Grund |
|---|---|---|---|---|---|---|---|
| `/runner/manual-runtime/failure-injection-matrix` | `runner_manual_runtime_failure_injection_matrix` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Diagnostic matrix, plan-only |
| `/runner/manual-runtime/failure-execution-preview` | `runner_manual_runtime_failure_execution_preview` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Preview, plan-only |
| `/runner/manual-runtime/failure-operator-checklists` | `runner_manual_runtime_failure_operator_checklists` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Checklists, plan-only |
| `/runner/manual-runtime/failure-test-sessions` | `runner_manual_runtime_failure_test_sessions` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Sessions, plan-only |
| `/runner/manual-runtime/failure-readiness-gate` | `runner_manual_runtime_failure_readiness_gate` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Readiness gate, plan-only |
| `/runtime-identifier-zero-state-verification` | `runner_runtime_identifier_zero_state_verification` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Verification, plan-only |
| `/runner/audit/sudoers` | — (Helper) | — | — | — | nein | **nein** | Kein Registry-runner_id, Facade-Mapping unklar |
| `/runner/privileged-validation/test-plan` | `runner_privileged_validation_test_plan` | MED | OPERATOR | blocked_operator_required | nein | **nein** | Operator-Gate |
| `/runner/lab-readiness/status` | `runner_lab_readiness_status` | MED | OPERATOR | blocked_operator_required | nein | **nein** | Operator-Gate |
| `/runner/manual-runtime/precheck` | `runner_manual_runtime_precheck` | MED | OPERATOR | blocked_operator_required | nein | **nein** | Operator-Gate |
| `/rescue/*validation*` | diverse | HIGH | — | — | nein | **nein** | Rescue-Domain unberührt |

## Ergebnis

6 sichere Kandidaten — siehe `DEPLOY_DIAGNOSTICS_ROUTER_SLICE_D8.md`.
