# Deploy Subrouter Inventory (Phase D.6)

**HEAD:** `d202abe` · **Modus:** Analyse only — keine Route verschoben

## routes.py (Orchestrator + Legacy-Monolith)

| Metrik | Wert |
|--------|------|
| Zeilen | **4821** |
| Direkte `from deploy.runner_*` Imports | **103** |
| Direkte `@router.*` Routen | **218** |
| `include_router` Subrouter | **4** |
| `build_plan_only_response` in routes.py | **0** |

## Subrouter (extrahiert D.2–D.5)

| Modul | Routen | GET | POST | Tag |
|-------|--------|-----|------|-----|
| `routes_registry.py` | 5 | 5 | 0 | `deploy-runners-registry` |
| `routes_risk_gate.py` | 5 | 5 | 0 | `deploy-runners-risk-gate` |
| `routes_evidence.py` | 6 | 0 | 6 | `deploy-evidence` |
| `routes_governance.py` | 3 | 0 | 3 | `deploy-governance` |
| **Summe Subrouter** | **19** | **10** | **9** | |

## Gesamt-API

| Metrik | Wert |
|--------|------|
| Routen gesamt | **237** (218 + 19) |
| Alle decoupled C.5/C.6 | in Subroutern |

## Domänen verbleibend in routes.py (218 Routen, heuristisch)

| Domain | ~Routen |
|--------|---------|
| rescue | 91 |
| evidence | 32 |
| governance | 31 |
| rescue_build | 18 |
| versioning | 16 |
| runtime | 13 |
| unknown | 17 |

## CSV

Vollständige Subrouter-Zeilen: `DEPLOY_SUBROUTER_INVENTORY_D6.csv` (19 Einträge)
