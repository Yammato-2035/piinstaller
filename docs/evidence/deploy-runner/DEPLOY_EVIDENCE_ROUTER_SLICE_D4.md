# Deploy Evidence Router Slice (Phase D.4)

## Gewählter Slice (6 Routen)

| Route | runner_id | Phase |
|-------|-----------|-------|
| POST /legacy-identifier-inventory | runner_legacy_identifier_inventory | C.5 |
| POST /legacy-identifier-hotspot-analysis | runner_legacy_identifier_hotspot_analysis | C.6 |
| POST /setuphelfer-identifier-consistency-check | runner_setuphelfer_identifier_consistency_check | C.6 |
| POST /runner/manual-runtime/evidence-timeline | runner_manual_runtime_evidence_timeline | C.6 |
| POST /runner/manual-runtime/evidence-final-snapshot | runner_manual_runtime_evidence_final_snapshot | C.6 |
| POST /runner/manual-runtime/result-validator-seal-index | runner_manual_runtime_validator_seal_index | C.6 |

**Modul:** `backend/deploy/routes_evidence.py`  
**Mechanismus:** `build_plan_only_response` — keine Runner-Imports

## Ausgeschlossen

| Route | Grund |
|-------|-------|
| /runner/next-phase/gate | Governance, nicht Evidence |
| /version-governance/state | Versioning |
| /version-source-of-truth-check | Versioning |
| seal-consistency-audit | Direkter Runner, nicht Facade |
| Alle Execute/Write-Routen | CRITICAL |

## Verbleiben in routes.py

- 3 decoupled C.5-Routen (Governance/Versioning)
- Alle nicht-decoupled Evidence-/Runtime-Routen
- Rescue/Deploy/Execute-Pfade unverändert
