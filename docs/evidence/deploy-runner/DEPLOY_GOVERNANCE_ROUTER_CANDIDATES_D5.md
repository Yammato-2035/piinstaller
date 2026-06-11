# Deploy Governance Router Candidates (Phase D.5)

**HEAD:** `c58e517`

| Route | runner_id | risk_level | execution_policy | C.4 Decision | bereits decoupled | D.5 geeignet | Grund |
|-------|-----------|------------|------------------|--------------|-------------------|--------------|-------|
| POST /runner/next-phase/gate | runner_next_phase_gate | evidence_write | lab_only | allowed_plan_only | ja (C.5) | **ja** | Facade plan-only |
| POST /version-governance/state | runner_version_governance | evidence_write | lab_only | allowed_plan_only | ja (C.5) | **ja** | Facade plan-only |
| POST /version-source-of-truth-check | runner_version_source_of_truth_check | evidence_write | lab_only | allowed_plan_only | ja (C.5) | **ja** | Facade plan-only |
| POST /runner/release/readiness | runner_release_readiness | evidence_write | lab_only | nein | nein | nein | Direkter Runner |
| POST /setuphelfer-controlled-rewrite-apply | — | system_change | operator_confirmed | blocked | nein | nein | Apply |

**Verbleibende C.5 decoupled in routes.py vor D.5:** genau 3 Routen (oben).
