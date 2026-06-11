# Deploy Routes Size After D.9

| Metrik | vorher (D.8) | nachher (D.9) |
|---|---:|---:|
| `routes.py` Zeilen | 4523 | **4523** (unverändert) |
| `routes_notifications.py` | — | **nicht angelegt** |
| direkte `runner_*`-Imports in `routes.py` | 93 | **93** |
| Subrouter | 5 | **5** |
| Extraktion | — | **no_safe_d9_notifications_slice** |
| OpenAPI-Pfade unverändert | — | **ja** (keine Änderung) |
| `allowed_to_execute` | false | **false** |
