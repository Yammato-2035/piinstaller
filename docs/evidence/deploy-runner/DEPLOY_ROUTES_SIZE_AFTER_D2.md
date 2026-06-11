# Deploy Routes Size After D.2

| Metrik | Vor D.2 | Nach D.2 |
|--------|---------|----------|
| `routes.py` Zeilen | 5041 | **5013** (−28) |
| `routes_registry.py` Zeilen | — | **46** |
| Registry GET-Routen in routes.py | 5 | **0** |
| Registry GET-Routen gesamt | 5 | **5** (in Subrouter) |
| Direkte `runner_*`-Imports routes.py | 104 | **104** (unverändert) |
| Gesamt-Routen | 237 | **237** |

## OpenAPI-Pfade

**Unverändert:** ja — gleiche URLs unter `/api/deploy/runners/*`

## Tags

Verbessert: `deploy-runners-registry` am Subrouter (kosmetisch für Swagger).
