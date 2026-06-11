# Deploy Risk-Gate Router Extraction (Phase D.3)

**Modul:** `backend/deploy/routes_risk_gate.py`  
**Status:** erledigt

## Extrahierte Routen (5 GET)

- `/api/deploy/runners/risk-gate/summary`
- `/api/deploy/runners/risk-gate/operator-required`
- `/api/deploy/runners/risk-gate/never-auto`
- `/api/deploy/runners/risk-gate/plan-allowed`
- `/api/deploy/runners/{runner_id}/risk-gate`

## Warum Risk-Gate nach Registry?

Zweitniedrigstes Risiko (D.1): nur Facade, GET-only, keine `runner_*`-Imports — analog D.2.

## allowed_to_execute

Bleibt **false** (C.4). Router führt keine Ausführung ein.

## Nächster Schritt D.4

`routes_evidence.py` — Evidence-/Plan-only-POST-Routen (Teilmenge).

## D.6 (Orchestrator-Target)

Keine weitere Extraktion — Thin-Orchestrator-Ziel dokumentiert (`DEPLOY_ROUTES_THIN_ORCHESTRATOR_TARGET_D6.md`).
