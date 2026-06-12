# APP Router Slice Candidate Audit — Phase E.7

**Baseline HEAD:** `72a7c93` · **Audit-only** (keine Extraktion)

## Ziel

Nach E.1–E.6 (26 extrahierte GET-Routen) prüfen, welche der verbleibenden **187** `@app.*` Routen sicher extrahierbar sind — und welche Facades zuerst nötig sind.

## Ergebnis

| Metrik | Wert |
|--------|------|
| `app.py` Zeilen | 17.472 |
| Verbleibende Routen | 187 |
| Bereits extrahiert (E.1–E.6) | 26 |
| Sichere E.8-Kandidaten | **3** |
| Blockiert (Facade/Core) | 4 Pflicht + 8 DCC-Aggregation |
| `unsafe` (Write/Backup/Rescue/…) | 109 |

## Sichere E.8-Kandidaten

Erweiterung `api/routes/dev_dashboard_readonly.py`:

1. `GET /api/dev-dashboard/backend-health`
2. `GET /api/dev-dashboard/notifications/status`
3. `GET /api/dev-dashboard/notifications/events`

## Blockiert (kein E.8/E.9 ohne Facade)

- `GET /api/status`, `GET /api/system/network`
- `GET /api/dev-dashboard/status`, `GET /api/dev-dashboard/roadmap`
- Backup/Restore/Deploy/Rescue/Partition-Write

## Guards (E.7)

`scripts/check-module-boundaries.sh` — neue WARN-only Tokens dokumentiert in `BOUNDARY_WARNINGS_E7.txt`.

## Evidence

- [APP_ROUTE_RESCAN_E7.md](../evidence/app-monolith/APP_ROUTE_RESCAN_E7.md)
- [APP_SAFE_NEXT_SLICES_E7.md](../evidence/app-monolith/APP_SAFE_NEXT_SLICES_E7.md)
- [APP_BLOCKED_ROUTES_E7.md](../evidence/app-monolith/APP_BLOCKED_ROUTES_E7.md)
- [APP_NEXT_FACADE_CANDIDATES_E7.md](./APP_NEXT_FACADE_CANDIDATES_E7.md)

## Nächster Schritt

**E.8** — Extraktion der 3 DCC read-only GETs **oder** Facade-Phase für System/DCC Status (parallel planbar, nicht mischen).
