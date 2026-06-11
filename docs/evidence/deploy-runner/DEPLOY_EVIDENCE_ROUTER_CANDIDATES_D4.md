# Deploy Evidence Router Candidates (Phase D.4)

**HEAD:** `31687df` · statische Analyse

## Pflichttabelle

| Route | runner_id | risk_level | execution_policy | C.4 Decision | bereits decoupled | D.4 geeignet | Grund |
|-------|-----------|------------|------------------|--------------|-------------------|--------------|-------|
| POST /legacy-identifier-inventory | runner_legacy_identifier_inventory | evidence_write | lab_only | allowed_plan_only | ja (C.5) | **ja** | Facade plan-only |
| POST /legacy-identifier-hotspot-analysis | runner_legacy_identifier_hotspot_analysis | evidence_write | lab_only | allowed_plan_only | ja (C.6) | **ja** | Facade plan-only |
| POST /setuphelfer-identifier-consistency-check | runner_setuphelfer_identifier_consistency_check | evidence_write | lab_only | allowed_plan_only | ja (C.6) | **ja** | Facade plan-only |
| POST /runner/manual-runtime/evidence-timeline | runner_manual_runtime_evidence_timeline | evidence_write | lab_only | allowed_plan_only | ja (C.6) | **ja** | Facade plan-only |
| POST /runner/manual-runtime/evidence-final-snapshot | runner_manual_runtime_evidence_final_snapshot | evidence_write | lab_only | allowed_plan_only | ja (C.6) | **ja** | Facade plan-only |
| POST /runner/manual-runtime/result-validator-seal-index | runner_manual_runtime_validator_seal_index | evidence_write | lab_only | allowed_plan_only | ja (C.6) | **ja** | Facade plan-only |
| POST /runner/next-phase/gate | runner_next_phase_gate | evidence_write | lab_only | allowed_plan_only | ja (C.5) | nein | Governance, nicht Evidence-Slice |
| POST /version-governance/state | runner_version_governance | evidence_write | lab_only | allowed_plan_only | ja (C.5) | nein | Versioning-Domain |
| POST /version-source-of-truth-check | runner_version_source_of_truth_check | evidence_write | lab_only | allowed_plan_only | ja (C.5) | nein | Versioning-Domain |
| POST /runner/manual-runtime/result-validator-seal-consistency-audit | runner_manual_runtime_validator_seal_consistency_audit | evidence_write | lab_only | allowed_plan_only | nein | nein | Direkter Runner-Aufruf |

## Ausgeschlossen (Stichproben)

- Execute/Write/Apply-Routen — CRITICAL
- Rescue/USB/ISO — HIGH
- Nicht-decoupled Evidence-Routen — Response-Kompatibilität unklar
