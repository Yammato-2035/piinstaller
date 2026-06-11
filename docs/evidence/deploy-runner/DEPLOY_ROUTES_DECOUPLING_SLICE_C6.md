# Deploy Routes Decoupling Slice C.6

| Route | runner_id | risk_level | execution_policy | C.4 Decision | C.6-Aktion | Grund |
|-------|-----------|------------|------------------|--------------|------------|-------|
| `POST /legacy-identifier-hotspot-analysis` | `runner_legacy_identifier_hotspot_analysis` | evidence_write | lab_only | allowed_plan_only | Facade | Identifier-Analyse, kein Execute |
| `POST /setuphelfer-identifier-consistency-check` | `runner_setuphelfer_identifier_consistency_check` | evidence_write | lab_only | allowed_plan_only | Facade | Read-only Check-Plan |
| `POST /runner/manual-runtime/evidence-timeline` | `runner_manual_runtime_evidence_timeline` | evidence_write | lab_only | allowed_plan_only | Facade | Evidence-Template |
| `POST /runner/manual-runtime/evidence-final-snapshot` | `runner_manual_runtime_evidence_final_snapshot` | evidence_write | lab_only | allowed_plan_only | Facade | Evidence-Snapshot-Plan |
| `POST /runner/manual-runtime/result-validator-seal-index` | `runner_manual_runtime_validator_seal_index` | evidence_write | lab_only | allowed_plan_only | Facade | Validator-Index-Plan |

`facade_decoupling_c6: true`, `allowed_to_execute: false`
