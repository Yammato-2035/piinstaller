# Deploy Routes Size After D.4

| Metrik | Vor D.4 | Nach D.4 |
|--------|---------|----------|
| `routes.py` Zeilen | 4981 | **4876** (−105) |
| `routes_evidence.py` Zeilen | — | **127** |
| Evidence plan-only in routes.py | 6 | **0** |
| Direkte `runner_*`-Imports | 104 | **104** |
| Gesamt-Routen | 237 | **237** |

## OpenAPI-Pfade

**Unverändert:** ja — POST-Pfade und Methoden identisch

## allowed_to_execute

**Weiterhin false** via `build_plan_only_response` + C.4 Risk Gate
