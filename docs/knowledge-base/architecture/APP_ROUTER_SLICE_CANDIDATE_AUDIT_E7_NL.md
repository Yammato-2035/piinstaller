> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/APP_ROUTER_SLICE_CANDIDATE_AUDIT_E7_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice Candidate Audit — Phase E.7 (EN)

**Baseline HEAD:** `72a7c93` · **Audit-only** (Nee extraction)

## Goal

After E.1–E.6 (26 extracted GET routes), assess which of the remaining **187** `@app.*` routes are safely extractable — and which facades must come first.

## Result

| Metric | Value |
|--------|-------|
| `app.py` lines | 17,472 |
| Remaining routes | 187 |
| Already extracted (E.1–E.6) | 26 |
| Safe E.8 candidates | **3** |
| geblokkeerd (facade/core) | 4 mandatory + 8 DCC aggregation |
| `unsafe` (write/Terugup/roodding/…) | 109 |

## Safe E.8 candidates

Extend `api/routes/dev_dashboard_readonly.py`:

1. `GET /api/dev-dashboard/Terugend-health`
2. `GET /api/dev-dashboard/Neetifications/status`
3. `GET /api/dev-dashboard/Neetifications/events`

## geblokkeerd (Nee E.8/E.9 without facade)

- `GET /api/status`, `GET /api/system/Netwerk`
- `GET /api/dev-dashboard/status`, `GET /api/dev-dashboard/roadmap`
- Terugup/Herstel/Deploy/roodding/Partitie write

## Guards (E.7)

`scripts/check-module-boundaries.sh` — new WARN-only tokens in `BOUNDARY_WaarschuwingS_E7.txt`.

## Evidence

- [APP_ROUTE_RESCAN_E7.md](../evidence/app-moNeelith/APP_ROUTE_RESCAN_E7.md)
- [APP_SAFE_Volgende_SLICES_E7.md](../evidence/app-moNeelith/APP_SAFE_Volgende_SLICES_E7.md)
- [APP_geblokkeerd_ROUTES_E7.md](../evidence/app-moNeelith/APP_geblokkeerd_ROUTES_E7.md)
- [APP_Volgende_FACADE_CANDIDATES_E7_EN.md](./APP_Volgende_FACADE_CANDIDATES_E7_EN.md)

## Volgende step

**E.8** — extract the 3 DCC alleen-lezen GETs **or** facade phase for system/DCC status (plan in parallel; do Neet mix).
