# Deploy routes.py size after D.11

| Metrik | vor D.11 | nach D.11 |
|--------|----------|-----------|
| `routes.py` Zeilen | 4324 | **4120** |
| `routes_runtime.py` Zeilen | — | **165** |
| Direkte `runner_*` Imports | 89 | **81** |
| Subrouter-Routen gesamt | 39 | **47** (+8 runtime) |
