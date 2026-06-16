# APP Router Slice E.10

**Status:** AKTIV (2026-06-16)  
**Version:** 1.8.7.0

## Ziel

System-Probe-GETs und sichere System-POST-Aktionen aus `app.py` extrahieren.

## Extrahiert (5)

| Route | Methode |
|-------|---------|
| `/api/system/paths` | GET |
| `/api/system/devices` | GET |
| `/api/system/terminal-available` | GET |
| `/api/system/reboot` | POST |
| `/api/system/packagekit/stop` | POST |

## Module

- `api/routes/system.py`
- `core/system_handlers.py`
- `core/system_runtime.py`

## Verbleibend in app.py

`/api/system/status`, resources, updates, asus-rog, mixer, freenove-detection, …

## Tests

- `backend/tests/test_app_router_slice_e10.py`
