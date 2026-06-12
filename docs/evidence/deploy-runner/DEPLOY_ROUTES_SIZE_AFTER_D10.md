# Deploy routes.py size after D.10

| Metrik | vor D.10 | nach D.10 |
|--------|----------|-----------|
| `routes.py` Zeilen | 4523 | **4324** |
| `routes_versioning.py` Zeilen | — | **165** |
| Direkte `runner_*` Imports in `routes.py` | 93 | **89** |
| Subrouter-Routen gesamt | 31 | **39** (+8 versioning) |
| Extrahierte D.10-Routen | 0 | **8** |

Evidence: `DEPLOY_VERSIONING_ROUTER_SLICE_D10.md`
