# Dev-Dashboard Timeout-Isolation

**Datum:** 2026-05-28

## Umgesetzt

1. **`_bounded_section`** in `backend/core/dev_dashboard.py` für `deploy_drift` (8s) und `cockpit_enrich` (10s).
2. **`/api/dev-dashboard/status`** in `asyncio.to_thread` mit 50s Gesamt-Timeout; bei Timeout degraded Body (kein 500, kein leerer Worker-Hang für andere Routen im Idealfall).
3. **`/health` / `/api/version`** über `core.liveness` — kein Dashboard-Import.

## Verhalten bei Timeout

- Abschnitt: `status=gray`, `warning=section_timeout_or_unavailable`.
- Gesamt-Status: `status=degraded`, `warning=dashboard_status_timeout`.

## JSON

`dev_dashboard_timeout_isolation_audit_latest.json`
