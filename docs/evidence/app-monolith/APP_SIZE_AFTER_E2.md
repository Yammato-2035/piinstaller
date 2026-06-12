# APP Size After E.2

| Metrik | E.1 (`0be2ab0`) | Nach E.2 |
|--------|-----------------|----------|
| `backend/app.py` Zeilen | 17.779 | 17.699 (−80) |
| `@app.*` Routen | 209 | 204 (−5) |
| `include_router(` Aufrufe | 20 | 22 (+2) |

## Kumulativ (E.1 + E.2)

| Metrik | Vor E.1 (`5a8a54c`) | Nach E.2 |
|--------|---------------------|----------|
| Zeilen | 17.857 | 17.699 (−158) |
| Routen | 213 | 204 (−9) |

## Router-Dateien (app slices)

| Datei | Routen | Phase |
|-------|--------|-------|
| `health.py` | 3 | E.1 |
| `version.py` | 1 | E.1 |
| `settings.py` | 2 | E.2 |
| `status.py` | 3 | E.2 |

Boundary: [BOUNDARY_WARNINGS_E2.txt](./BOUNDARY_WARNINGS_E2.txt)
