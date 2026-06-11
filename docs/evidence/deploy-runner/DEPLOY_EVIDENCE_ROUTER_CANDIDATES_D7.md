# Deploy Evidence Router Candidates (Phase D.7)

**HEAD:** d102b08 (vor D.7)  
**Analyse:** `backend/deploy/routes.py` — Keyword-Scan + Risk-Gate

## Zulässigkeitskriterien

- `allowed_plan_only` / `evidence_write` / `read_only`
- kein sudo, kein device_write, kein destructive, kein system_change
- kein Execute-/Apply-/Write-/Rescue-Build-/USB-Pfad
- abbildbar via `build_plan_only_response`

## Kandidaten-Tabelle

| Route | runner_id | risk_level | execution_policy | C.4 Decision | bereits decoupled | D.7 geeignet | Grund |
|---|---|---|---|---|---|---|---|
| `/legacy-identifier-cleanup-classification` | `runner_legacy_identifier_cleanup_classifier` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Identifier-Klassifikation, plan-only |
| `/legacy-runtime-compatibility-inventory` | `runner_legacy_runtime_compatibility_validation` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Inventory, plan-only |
| `/legacy-runtime-coexistence-analysis` | `runner_legacy_runtime_compatibility_validation` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Analyse, plan-only |
| `/runner/manual-runtime/failure-test-results` | `runner_manual_runtime_failure_test_result_capture` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Result-Capture plan-only |
| `/runner/manual-runtime/failure-result-evaluation` | `runner_manual_runtime_failure_result_evaluation` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Evaluation plan-only |
| `/runner/manual-runtime/result-validator-seal-consistency-audit` | `runner_manual_runtime_validator_seal_consistency_audit` | LOW | LAB_ONLY | allowed_plan_only | nein | **ja** | Audit plan-only |
| `/rescue/recovery-evidence-timeline` | `runner_rescue_recovery_evidence_timeline` | HIGH | LAB_ONLY | allowed_plan_only | nein | **nein** | Rescue-Domain — unberührt |
| `/rescue/component-inventory` | `runner_rescue_stick_component_inventory` | HIGH | LAB_ONLY | allowed_plan_only | nein | **nein** | Rescue/USB — unberührt |
| `/runner/manual-runtime/result-check` | `runner_manual_runtime_result_edit_checker` | MEDIUM | OPERATOR_CONFIRMED | blocked_operator_required | nein | **nein** | Operator-Gate |
| `/runner/manual-runtime/result-template` | `runner_manual_runtime_result_template` | MEDIUM | OPERATOR_CONFIRMED | blocked_operator_required | nein | **nein** | Operator-Gate |
| `/runner/manual-runtime/laptop-failure-evidence-timeline` | `runner_manual_runtime_laptop_failure_evidence_timeline` | LOW | LAB_ONLY | allowed_plan_only | nein | **nein** | Slice auf 6 begrenzt; D.8+ |
| `/legacy-runtime-safe-migration-recommendations` | `runner_legacy_runtime_compatibility_validation` | LOW | LAB_ONLY | allowed_plan_only | nein | **nein** | Governance-nah; Slice voll |

## Ergebnis

6 sichere Kandidaten für D.7 — siehe `DEPLOY_EVIDENCE_ROUTER_SLICE_D7.md`.
