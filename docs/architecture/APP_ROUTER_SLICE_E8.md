# APP Router Slice E.8

**Baseline HEAD:** `cdc391e` · **Status:** erledigt

## Extrahierte Routen (3)

Erweiterung von `api/routes/dev_dashboard_readonly.py`:

- `GET /api/dev-dashboard/backend-health` → `core.dev_dashboard_backend_health`
- `GET /api/dev-dashboard/notifications/status` → `core.notification_state`
- `GET /api/dev-dashboard/notifications/events` → `core.notification_state`

Kein `build_dashboard_status`. Keine neue Notification-State-Logik im Router.

## Metriken

`app.py`: 17.472 → 17.425 Zeilen; 187 → 184 Routen.

## Nächster Schritt

**F.2** — DCC Status Facade (status route bereits im readonly router). **E.9** — control-center Router-Slice.
