> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/DEPLOY_RISK_GATE_ROUTER_EXTRACTION_D3_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Risk-Gate Router Extraktion (Phase D.3)

**Module:** `backend/deploy/routes_risk_gate.py`  
**Stand:** complete

## Extracted routes (5 GET)

- `/api/deploy/runners/risk-gate/summary`
- `/api/deploy/runners/risk-gate/operator-erforderlich`
- `/api/deploy/runners/risk-gate/never-auto`
- `/api/deploy/runners/risk-gate/plan-allowed`
- `/api/deploy/runners/{runner_id}/risk-gate`

## Why risk gate after registry?

Second-lowest risk (D.1): facade only, GET-only, no `runner_*` imports — same pattern as D.2.

## allowed_to_execute

Stays **false** (C.4). Router introduces no execution.

## Next step D.4

`routes_evidence.py` — evidence/plan-only POST routes (subset).

## D.6 (orchestrator target)

No further extraction — thin orchestrator target documented (`DEPLOY_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).
