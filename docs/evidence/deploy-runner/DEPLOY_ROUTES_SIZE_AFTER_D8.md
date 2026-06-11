# Deploy Routes Size After D.8

| Metrik | vorher (D.7) | nachher (D.8) |
|---|---:|---:|
| `routes.py` Zeilen | 4671 | **4523** |
| `routes_diagnostics.py` Zeilen | — | **128** |
| Subrouter gesamt | 4 | **5** |
| direkte `runner_*`-Imports in `routes.py` | 99 | **93** |
| OpenAPI-Pfade unverändert | — | **ja** |
| `allowed_to_execute` | false | **false** |
