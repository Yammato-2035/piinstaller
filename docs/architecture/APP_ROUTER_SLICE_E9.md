# APP Router Slice E.9

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.6.0

## Ziel

Alle `/api/control-center/*` Routen (33) aus `app.py` in dedizierten Router extrahieren.

## Module

| Datei | Rolle |
|-------|-------|
| `api/routes/control_center.py` | HTTP-Router |
| `core/control_center_handlers.py` | Handler-Logik |
| `core/control_center_runtime.py` | Lazy-Adapter zu `app` (`sudo_store`, Module) |

## Metriken

- **33** Routen extrahiert (GET + POST)
- `app.py` −~600 Zeilen
- `_get_control_center_module()` bleibt in `app.py` (Legacy-Lazy-Loader)

## Tests

- `backend/tests/test_app_router_slice_e9.py`
- Regression: `test_control_center_bluetooth_status.py`
