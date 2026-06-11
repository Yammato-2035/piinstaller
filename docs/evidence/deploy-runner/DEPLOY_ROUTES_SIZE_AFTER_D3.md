# Deploy Routes Size After D.3

| Metrik | Vor D.3 | Nach D.3 |
|--------|---------|----------|
| `routes.py` Zeilen | 5013 | **4981** (−32) |
| `routes_risk_gate.py` Zeilen | — | **46** |
| Risk-Gate GET in routes.py | 5 | **0** |
| Risk-Gate GET gesamt | 5 | **5** (Subrouter) |
| Direkte `runner_*`-Imports routes.py | 104 | **104** |
| Gesamt-Routen | 237 | **237** |

## OpenAPI-Pfade

**Unverändert:** ja

## allowed_to_execute

**Weiterhin false** (C.4, via Facade/Risk-Gate-Modul)
