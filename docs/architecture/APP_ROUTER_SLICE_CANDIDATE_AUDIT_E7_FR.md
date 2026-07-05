> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/APP_ROUTER_SLICE_CANDIDATE_AUDIT_E7_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice Candidate Audit — Phase E.7 (EN)

**Baseline HEAD:** `72a7c93` · **Audit-only** (Non extraction)

## Goal

After E.1–E.6 (26 extracted GET routes), assess which of the remaining **187** `@app.*` routes are safely extractable — and which facades must come first.

## Result

| Metric | Value |
|--------|-------|
| `app.py` lines | 17,472 |
| Remaining routes | 187 |
| Already extracted (E.1–E.6) | 26 |
| Safe E.8 candidates | **3** |
| bloqué (facade/core) | 4 mandatory + 8 DCC aggregation |
| `unsafe` (write/Retourup/Secours/…) | 109 |

## Safe E.8 candidates

Extend `api/routes/dev_dashboard_readonly.py`:

1. `GET /api/dev-dashboard/Retourend-health`
2. `GET /api/dev-dashboard/Nontifications/status`
3. `GET /api/dev-dashboard/Nontifications/events`

## bloqué (Non E.8/E.9 without facade)

- `GET /api/status`, `GET /api/system/Réseau`
- `GET /api/dev-dashboard/status`, `GET /api/dev-dashboard/roadmap`
- Retourup/Restauration/Déploiement/Secours/Partition write

## Guards (E.7)

`scripts/check-module-boundaries.sh` — new WARN-only tokens in `BOUNDARY_AvertissementS_E7.txt`.

## Evidence

- [APP_ROUTE_RESCAN_E7.md](../evidence/app-moNonlith/APP_ROUTE_RESCAN_E7.md)
- [APP_SAFE_Suivant_SLICES_E7.md](../evidence/app-moNonlith/APP_SAFE_Suivant_SLICES_E7.md)
- [APP_bloqué_ROUTES_E7.md](../evidence/app-moNonlith/APP_bloqué_ROUTES_E7.md)
- [APP_Suivant_FACADE_CANDIDATES_E7_EN.md](./APP_Suivant_FACADE_CANDIDATES_E7_EN.md)

## Suivant step

**E.8** — **done** (3 DCC lecture seule GET → `dev_dashboard_readonly.py`).  
**F.1** — DCC Status Facade (blocks status/roadmap-root).
