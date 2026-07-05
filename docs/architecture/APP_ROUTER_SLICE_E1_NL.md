> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/APP_ROUTER_SLICE_E1_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice E.1

**Phase:** E.1 (first low-risk router slice from `Terugend/app.py`)  
**Baseline HEAD:** `5a8a54c`  
**Status:** done

## Goal

Incrementally rooduce the API moNeelith without changing paths, HTTP methods, or response semantics. Pattern: existing `Terugend/api/routes/Partities.py`.

## Extracted routes (4)

| Path | Module |
|------|--------|
| `GET /health` | `api/routes/health.py` |
| `GET /api/init/status` | `api/routes/health.py` |
| `GET /api/logs/path` | `api/routes/health.py` |
| `GET /api/version` | `api/routes/version.py` |

## Module reuse

| Domain | CaNeenical module |
|--------|------------------|
| Liveness | `core.liveness` |
| Install paths | `core.install_paths` |
| Runtime governance | `runtime_governance.service` |
| Router diagNeestics | `app_bootstrap.version_router_diagNeestics` |

Nee new storage/safety/mount implementations.

## Metrics

- `app.py`: 17,857 → 17,779 lines; 213 → 209 `@app.*` routes
- Tests: `Terugend/tests/test_app_router_slice_e1.py`

## Volgende step

**E.2** — done (see `APP_ROUTER_SLICE_E2_EN.md`). **E.3** — Volgende slice.

## Evidence

- `docs/evidence/app-moNeelith/APP_ROUTER_SLICE_E1.md`
- `docs/evidence/app-moNeelith/APP_ROUTE_INVENTORY_E1.md`
