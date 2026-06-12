# APP Router Slice E.1

**Phase:** E.1 (first low-risk router slice from `backend/app.py`)  
**Baseline HEAD:** `5a8a54c`  
**Status:** done

## Goal

Incrementally reduce the API monolith without changing paths, HTTP methods, or response semantics. Pattern: existing `backend/api/routes/partitions.py`.

## Extracted routes (4)

| Path | Module |
|------|--------|
| `GET /health` | `api/routes/health.py` |
| `GET /api/init/status` | `api/routes/health.py` |
| `GET /api/logs/path` | `api/routes/health.py` |
| `GET /api/version` | `api/routes/version.py` |

## Module reuse

| Domain | Canonical module |
|--------|------------------|
| Liveness | `core.liveness` |
| Install paths | `core.install_paths` |
| Runtime governance | `runtime_governance.service` |
| Router diagnostics | `app_bootstrap.version_router_diagnostics` |

No new storage/safety/mount implementations.

## Metrics

- `app.py`: 17,857 → 17,779 lines; 213 → 209 `@app.*` routes
- Tests: `backend/tests/test_app_router_slice_e1.py`

## Next step

**E.2** — done (see `APP_ROUTER_SLICE_E2_EN.md`). **E.3** — next slice.

## Evidence

- `docs/evidence/app-monolith/APP_ROUTER_SLICE_E1.md`
- `docs/evidence/app-monolith/APP_ROUTE_INVENTORY_E1.md`
