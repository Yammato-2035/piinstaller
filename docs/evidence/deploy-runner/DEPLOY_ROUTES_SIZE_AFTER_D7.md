# Deploy Routes Size After D.7

| Metrik | vorher (D.6) | nachher (D.7) |
|---|---:|---:|
| `routes.py` Zeilen | 4821 | **4671** |
| `routes_evidence.py` Zeilen | 128 | **235** |
| Evidence-Routen gesamt | 6 | **12** |
| Evidence-Routen in `routes.py` | 6 decoupled + ~32 | ~26 verbleibend |
| direkte `runner_*`-Imports in `routes.py` | 103 | **99** |
| OpenAPI-Pfade unverändert | — | **ja** |
| `allowed_to_execute` | false | **false** |
