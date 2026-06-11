# Deploy Routes Size After D.5

| Metrik | Vor D.5 | Nach D.5 |
|--------|---------|----------|
| `routes.py` Zeilen | 4876 | **4821** (−55) |
| `routes_governance.py` Zeilen | — | **94** |
| Governance decoupled in routes.py | 3 | **0** |
| Boundary `runner_*`-Import-Zählung routes.py | 104 | **103** (−1: `runner_api_facade` aus routes.py) |
| Ausführbare `runner_*.py`-Imports | 103 | **103** |
| Gesamt-Routen | 237 | **237** |

## OpenAPI-Pfade

**Unverändert:** ja

## allowed_to_execute

**Weiterhin false**
