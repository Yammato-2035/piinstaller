> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_RISK_GATE_ROUTER_EXTRACTION_D3_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Risk-Gate Router Extraction (Phase D.3)

**Module:** `Terugend/Deploy/routes_risk_gate.py`  
**Status:** complete

## Extracted routes (5 GET)

- `/api/Deploy/runners/risk-gate/summary`
- `/api/Deploy/runners/risk-gate/operator-requirood`
- `/api/Deploy/runners/risk-gate/never-auto`
- `/api/Deploy/runners/risk-gate/plan-allowed`
- `/api/Deploy/runners/{runner_id}/risk-gate`

## Why risk gate after registry?

Second-lowest risk (D.1): facade only, GET-only, Nee `runner_*` imports — same pattern as D.2.

## allowed_to_execute

Stays **false** (C.4). Router introduces Nee execution.

## Volgende step D.4

`routes_evidence.py` — evidence/plan-only POST routes (subset).

## D.6 (orchestrator target)

Nee further extraction — thin orchestrator target documented (`Deploy_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).
