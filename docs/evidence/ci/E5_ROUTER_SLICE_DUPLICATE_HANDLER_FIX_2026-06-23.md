# E5 Router Slice Duplicate-Handler Fix

## Ausgangsfehler
- **CI Run:** `28040489375`
- **Test:** `test_app_router_slice_e5.py::test_app_py_includes_router_and_no_duplicate_handlers`
- **Fehler:** `'@app.get("/api/dev-dashboard/roadmap")' not found in app.py`

## E5-Erwartung vs. Ist-Zustand

| E5-Erwartung | Ist-Zustand | Bewertung | Entscheidung |
|---|---|---|---|
| `include_router(dev_dashboard_roadmap_router)` in `app.py` | vorhanden | korrekt | beibehalten |
| Aggregat-Route `@app.get("/api/dev-dashboard/roadmap")` in `app.py` | **nicht** in `app.py` | nach E.10 in `control_center_readonly.py` ausgelagert | Test auf Router-Datei umstellen |
| Sub-Routen nicht dupliziert in `app.py` | keine `@app.get` für areas/milestones/… | korrekt | beibehalten |

## Runtime-Duplikatprüfung (`/api/dev-dashboard/roadmap*`)
- 8 Routen registriert, **0 Duplikate**
- Aggregat: `GET /api/dev-dashboard/roadmap` via `control_center_readonly_router`
- Registry-Slice: `dev_dashboard_roadmap_router` (areas, milestones, …)

## Contract-Entscheidung
**Test veraltet** — kein Code-/Duplicate-Fehler. E5-Ziel (keine doppelten Legacy-Handler in `app.py`) bleibt; Aggregat-Route lebt bewusst im Control-Center-Readonly-Router.

## Fix
- `backend/tests/test_app_router_slice_e5.py`: prüft `control_center_readonly_router`-Include und `@router.get("/api/dev-dashboard/roadmap")` in `control_center_readonly.py`; verboten bleibt `@app.get` in `app.py`.

## Lokale Checks

| Check | Ergebnis |
|---|---|
| `pytest tests/test_app_router_slice_e5.py` | grün |
| `pytest e4+e5+e11+fix9+anti_regression` | grün |
| `pip-audit` | grün |
| `npm audit --omit=dev --audit-level=high` | grün |

## Erwartetes CI-Ergebnis
- E5 bestanden; nächster Stopper vermutlich E6 (gleiche veraltete `@app.get("/api/dev-dashboard/roadmap")`-Anchor-Prüfung).
