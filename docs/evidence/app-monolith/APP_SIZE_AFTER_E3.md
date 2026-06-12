# APP Size After E.3

| Metrik | E.2 (`b667785`) | Nach E.3 |
|--------|-----------------|----------|
| `backend/app.py` Zeilen | 17.699 | 17.617 (−82) |
| `@app.*` Routen | 204 | 199 (−5) |
| `include_router(` | 22 | 24 (+2) |

## Kumulativ (E.1–E.3)

| Metrik | Vor E.1 | Nach E.3 |
|--------|---------|----------|
| Zeilen | 17.857 | 17.617 (−240) |
| Routen | 213 | 199 (−14) |

## Router-Module

| Datei | Routen gesamt | E.3 neu |
|-------|---------------|---------|
| `health.py` | 4 | +1 tail |
| `status.py` | 4 | +1 self-update |
| `catalog.py` | 1 | neu |
| `capabilities.py` | 2 | neu |
