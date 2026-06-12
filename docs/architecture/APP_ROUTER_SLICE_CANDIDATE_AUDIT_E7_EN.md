# APP Router Slice Candidate Audit — Phase E.7 (EN)

**Baseline HEAD:** `72a7c93` · **Audit-only** (no extraction)

## Goal

After E.1–E.6 (26 extracted GET routes), assess which of the remaining **187** `@app.*` routes are safely extractable — and which facades must come first.

## Result

| Metric | Value |
|--------|-------|
| `app.py` lines | 17,472 |
| Remaining routes | 187 |
| Already extracted (E.1–E.6) | 26 |
| Safe E.8 candidates | **3** |
| Blocked (facade/core) | 4 mandatory + 8 DCC aggregation |
| `unsafe` (write/backup/rescue/…) | 109 |

## Safe E.8 candidates

Extend `api/routes/dev_dashboard_readonly.py`:

1. `GET /api/dev-dashboard/backend-health`
2. `GET /api/dev-dashboard/notifications/status`
3. `GET /api/dev-dashboard/notifications/events`

## Blocked (no E.8/E.9 without facade)

- `GET /api/status`, `GET /api/system/network`
- `GET /api/dev-dashboard/status`, `GET /api/dev-dashboard/roadmap`
- Backup/Restore/Deploy/Rescue/Partition write

## Guards (E.7)

`scripts/check-module-boundaries.sh` — new WARN-only tokens in `BOUNDARY_WARNINGS_E7.txt`.

## Evidence

- [APP_ROUTE_RESCAN_E7.md](../evidence/app-monolith/APP_ROUTE_RESCAN_E7.md)
- [APP_SAFE_NEXT_SLICES_E7.md](../evidence/app-monolith/APP_SAFE_NEXT_SLICES_E7.md)
- [APP_BLOCKED_ROUTES_E7.md](../evidence/app-monolith/APP_BLOCKED_ROUTES_E7.md)
- [APP_NEXT_FACADE_CANDIDATES_E7_EN.md](./APP_NEXT_FACADE_CANDIDATES_E7_EN.md)

## Next step

**E.8** — **done** (3 DCC read-only GET → `dev_dashboard_readonly.py`).  
**F.1** — DCC Status Facade (blocks status/roadmap-root).
