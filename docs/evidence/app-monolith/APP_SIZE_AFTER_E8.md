# APP Size After E.8

**HEAD:** nach E.8 Extraktion

| Datei | Zeilen vorher (E.7) | Zeilen nachher | Δ |
|-------|---------------------|----------------|---|
| `backend/app.py` | 17.472 | 17.425 | −47 |
| `backend/api/routes/dev_dashboard_readonly.py` | 62 | 112 | +50 |

| Metrik | vorher | nachher |
|--------|--------|---------|
| `@app.*` Routen in `app.py` | 187 | 184 |
| `include_router` in `app.py` | 26 | 26 (unverändert) |
| Extrahierte GET-Routen kumulativ (E.1–E.8) | 26 | **29** |

Boundary: `app_py_route_count_reduced_e7:187_to_184`, `app_py_line_count_reduced_e7:17472_to_17425`
