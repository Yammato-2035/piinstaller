# E6 Router Slice Contract Fix

## Ausgangsfehler
- **CI Run:** `28041066000`
- **Test:** `test_app_router_slice_e6.py::test_app_py_no_duplicate_e6_handlers`
- **Fehler:** `'@app.get("/api/dev-dashboard/roadmap")' not found in app.py`

## E6-Erwartung alt/neu

| Alt | Neu |
|---|---|
| Aggregat `@app.get("/api/dev-dashboard/roadmap")` in `app.py` | `@router.get` in `control_center_readonly.py` |
| nur `dev_dashboard_roadmap_router` include | zusätzlich `control_center_readonly_router` include |
| E6-Sub-Routen nicht in `app.py` | unverändert |

## Same-Anchor-Scan

| Testdatei | Alter Anchor vorhanden | Fix nötig | Bemerkung |
|---|---|---|---|
| `test_app_router_slice_e5.py` | nein (bereits gefixt) | — | prüft `assertNotIn` + `cc_ro` |
| `test_app_router_slice_e6.py` | ja (`assertIn` app.py) | **ja** | gleicher E5-Pattern-Fix |
| `test_app_router_slice_e7`–`e14` | nein | — | kein `/roadmap`-app-Anchor |

## Runtime-Duplikatprüfung
- **ROADMAP_ROUTE_COUNT:** 8
- **DUPLICATES:** `[]`

## Fix
- `backend/tests/test_app_router_slice_e6.py` — E5-kompatibler Router-Contract-Guard

## Lokale Checks

| Check | Ergebnis |
|---|---|
| `pytest tests/test_app_router_slice_e6.py` | grün |
| `pytest e4+e5+e6+e11+fix9+anti_regression` | grün |
| `pip-audit` | grün |
| `npm audit --omit=dev --audit-level=high` | grün |

## Erwartetes CI-Ergebnis
- E6 bestanden; nächster Stopper ggf. weiterer Router-Slice-/Assertion-Test nach alphabetischem `-x`-Fortschritt.
