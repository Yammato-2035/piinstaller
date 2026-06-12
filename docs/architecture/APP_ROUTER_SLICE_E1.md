# APP Router Slice E.1

**Phase:** E.1 (erster risikoarmer Router-Slice aus `backend/app.py`)  
**HEAD:** nach `5a8a54c`  
**Status:** erledigt

## Ziel

Inkrementelle Entlastung des API-Monolithen ohne Pfad-, Methoden- oder Semantikänderung. Vorbild: bestehende `backend/api/routes/partitions.py`.

## Extrahierte Routen (4)

| Pfad | Modul |
|------|-------|
| `GET /health` | `api/routes/health.py` |
| `GET /api/init/status` | `api/routes/health.py` |
| `GET /api/logs/path` | `api/routes/health.py` |
| `GET /api/version` | `api/routes/version.py` |

## Module-Reuse

| Domäne | Canonical |
|--------|-----------|
| Liveness | `core.liveness` |
| Install-Pfade | `core.install_paths` |
| Runtime-Governance | `runtime_governance.service` |
| Router-Diagnostik | `app_bootstrap.version_router_diagnostics` |

Keine neuen Storage-/Safety-/Mount-Implementierungen.

## Metriken

- `app.py`: 17.857 → 17.779 Zeilen, 213 → 209 `@app.*` Routen
- Tests: `backend/tests/test_app_router_slice_e1.py`
- Boundary: `app_py_line_count_reduced_e1`, `app_py_route_count`

## Nächster Schritt

**E.2** — erledigt (siehe `APP_ROUTER_SLICE_E2.md`). **E.3** — nächster Slice.

## Evidence

- `docs/evidence/app-monolith/APP_ROUTER_SLICE_E1.md`
- `docs/evidence/app-monolith/APP_ROUTE_INVENTORY_E1.md`
