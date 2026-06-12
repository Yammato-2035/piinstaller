# APP Router Slice E.8 (EN)

**Baseline HEAD:** `cdc391e` · **Status:** done

## Extracted routes (3)

Extension of `api/routes/dev_dashboard_readonly.py`:

- `GET /api/dev-dashboard/backend-health` → `core.dev_dashboard_backend_health`
- `GET /api/dev-dashboard/notifications/status` → `core.notification_state`
- `GET /api/dev-dashboard/notifications/events` → `core.notification_state`

No `build_dashboard_status`. No new notification state logic in the router.

## Metrics

`app.py`: 17,472 → 17,425 lines; 187 → 184 routes.

## Next step

**F.1** — DCC Status Facade.
