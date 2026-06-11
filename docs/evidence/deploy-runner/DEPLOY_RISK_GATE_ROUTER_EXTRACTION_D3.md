# Deploy Risk-Gate Router Extraction (Phase D.3)

**Datum:** 2026-06-10  
**HEAD vorher:** `16b0657`  
**Modus:** Router-Extraktion, keine Runner-Ausführung

## Extrahierte Routen

| Zeilen (alt routes.py) | Route | Facade-Funktion |
|------------------------|-------|-----------------|
| 4991–4993 | `GET /runners/risk-gate/summary` | `build_runner_risk_gate_summary()` |
| 4996–4998 | `GET /runners/risk-gate/operator-required` | `list_runner_operator_required()` |
| 5001–5003 | `GET /runners/risk-gate/never-auto` | `list_runner_never_auto()` |
| 5006–5008 | `GET /runners/risk-gate/plan-allowed` | `list_runner_plan_allowed()` |
| 5011–5013 | `GET /runners/{runner_id}/risk-gate` | `get_runner_risk_gate_decision()` |

**Öffentliche Pfade:** `/api/deploy/runners/*` — unverändert

## Imports

| Modul | Imports |
|-------|---------|
| `routes_risk_gate.py` | nur `deploy.runner_api_facade` |
| `routes.py` (entfernt) | alle 5 Risk-Gate-Facade-Symbole |

## Semantik

| Prüfung | Ergebnis |
|---------|----------|
| Response-Semantik stabil | **ja** |
| Pfade unverändert | **ja** |
| Keine Runner-Imports nötig | **ja** |
| Keine Execute-Semantik | **ja** — `allowed_to_execute` bleibt **false** (C.4) |

## Einbindung

```python
from deploy.routes_risk_gate import router as deploy_risk_gate_router
router.include_router(deploy_risk_gate_router)
```

Nach `deploy_registry_router` (D.2).
