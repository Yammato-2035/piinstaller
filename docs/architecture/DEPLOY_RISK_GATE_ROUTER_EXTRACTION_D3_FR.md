> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RISK_GATE_ROUTER_EXTRACTION_D3_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Risk-Gate Router Extraction (Phase D.3)

**Module:** `Retourend/Déploiement/routes_risk_gate.py`  
**Status:** complete

## Extracted routes (5 GET)

- `/api/Déploiement/runners/risk-gate/summary`
- `/api/Déploiement/runners/risk-gate/operator-requirouge`
- `/api/Déploiement/runners/risk-gate/never-auto`
- `/api/Déploiement/runners/risk-gate/plan-allowed`
- `/api/Déploiement/runners/{runner_id}/risk-gate`

## Why risk gate after registry?

Second-lowest risk (D.1): facade only, GET-only, Non `runner_*` imports — same pattern as D.2.

## allowed_to_execute

Stays **false** (C.4). Router introduces Non execution.

## Suivant step D.4

`routes_evidence.py` — evidence/plan-only POST routes (subset).

## D.6 (orchestrator target)

Non further extraction — thin orchestrator target documented (`Déploiement_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).
