# Deploy Thin-Orchestrator Audit — D.12

**Datum:** 2026-06-10  
**HEAD (Start):** 23462c1  
**Datei:** `backend/deploy/routes.py` (~4120 Zeilen)

## Kennzahlen

| Metrik | Wert |
|--------|------|
| HTTP-Routen (`@router.*`) | 190 |
| Direkte `from deploy.runner_*` Imports | 81 |
| `from deploy.*` Imports gesamt | ~100 |
| Subrouter (`include_router`) | 7 |

## Subrouter

- `deploy_registry_router`
- `deploy_risk_gate_router`
- `deploy_evidence_router`
- `deploy_governance_router`
- `deploy_diagnostics_router`
- `deploy_versioning_router`
- `deploy_runtime_router`

## Domain-Verteilung (Pfad-Segment 1)

| Domain | Routen |
|--------|--------|
| rescue | 99 |
| runner | 47 |
| rescue-stick | 10 |
| write | 6 |
| cache | 3 |
| hardware-gate | 2 |
| final-confirmation | 2 |
| real-write | 2 |
| plan / session / execute / preview | je 1 |

## Verbleibende Runner-Imports

81 direkte `from deploy.runner_*` in `routes.py` (Orchestrator-Monolith).

## D.12 Extraktion

Keine weiteren sicheren plan-only/readonly-Slices in diesem Lauf identifiziert — nur Dokumentation.

Siehe `DEPLOY_THIN_ORCHESTRATOR_FINAL_PLAN.md`
