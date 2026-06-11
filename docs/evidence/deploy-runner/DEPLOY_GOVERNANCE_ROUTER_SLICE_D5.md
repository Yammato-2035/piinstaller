# Deploy Governance Router Slice (Phase D.5)

## Gewählt (3 Routen — kompletter C.5-Rest)

| Route | runner_id |
|-------|-----------|
| POST /runner/next-phase/gate | runner_next_phase_gate |
| POST /version-governance/state | runner_version_governance |
| POST /version-source-of-truth-check | runner_version_source_of_truth_check |

**Modul:** `backend/deploy/routes_governance.py`

## Ausgeschlossen

Release-/Deploy-Execute, Apply-Routen, nicht-decoupled Governance-Handler.

## routes.py nach D.5

- **Kein** `build_plan_only_response` mehr in `routes.py`
- Alle 9 C.5/C.6 decoupled Routen in Subroutern (6 Evidence + 3 Governance)
- Facade-Import nur noch in Subroutern
