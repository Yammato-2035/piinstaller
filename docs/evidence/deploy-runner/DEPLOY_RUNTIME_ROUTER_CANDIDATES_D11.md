# Deploy Runtime Router Candidates (D.11)

**HEAD:** `ea92fa9` (vor D.11) · **Module-Reuse:** M.1 geprüft

## Pflichttabelle (Auszug)

| Route | Methode | runner_id | risk_level | execution_policy | C.4 Decision | Runtime-Änderung? | D.11 geeignet | Grund |
|---|---|---|---|---|---|---|---|---|
| POST `/plan` | POST | core_deploy | read_only | lab_only | — | nein | **nein** | Core deploy execute chain |
| POST `/execute` | POST | — | device_write | operator_confirmed | BLOCKED | **ja** | **nein** | Execute |
| POST `/runner/lab-readiness/status` | POST | runner_lab_readiness_status | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Status read-only via Facade |
| POST `/runner/runtime-runbook/bundle` | POST | runner_runtime_runbook_bundle | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Runbook bundle |
| POST `/runner/runtime-runbook/export` | POST | runner_runtime_runbook_export | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **ja** | Export plan-only |
| POST `/runner/runtime-results/validate` | POST | runner_runtime_result_validator | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Validation only |
| POST `/runner/lab-readiness/acceptance` | POST | runner_lab_acceptance_aggregator | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Acceptance summary |
| POST `/runner/lab-phase/consolidation` | POST | runner_lab_phase_consolidation | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Consolidation status |
| POST `/runner/release/readiness` | POST | runner_release_readiness | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Readiness matrix |
| POST `/runner/lab-readiness/unblock-plan` | POST | runner_lab_readiness_plan | local_runtime_change | operator_confirmed | ALLOWED_PLAN_ONLY | nein | **ja** | Plan only |
| POST `/runner/lab-readiness/acceptance/export` | POST | runner_lab_acceptance_report_export | evidence_write | lab_only | ALLOWED_PLAN_ONLY | nein | **später** | Slice voll (8) |
| POST `/runner/manual-runtime/laptop-live-probe-execute-readonly` | POST | — | — | — | — | **ja** | **nein** | Execute im Pfad |
| POST `/runner/sudoers/runtime-test-plan` | POST | runner_sudoers_runtime_test_plan | — | — | — | nein | **nein** | Diagnostics-Domäne, sudo |

## Ausgeschlossen

restart, deploy-to-opt, apply, install, write, execute, systemctl, sudo, package install, profile switch
