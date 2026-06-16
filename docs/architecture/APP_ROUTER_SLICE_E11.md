# App Router Slice E.11

**Phase:** Monolith-Auflösung — System GET-Slice 11  
**Version:** 1.8.8.0

## Scope

Sechs read-only GET-Routen aus `app.py` nach `system.py` / `system_handlers.py`:

| Route | Handler |
|-------|---------|
| `GET /api/system/service-conflicts` | `get_service_conflicts` |
| `GET /api/system/resources` | `get_system_resources` |
| `GET /api/system/installed-packages` | `get_installed_packages` |
| `GET /api/system/running-processes` | `get_running_processes_endpoint` |
| `GET /api/system/security-config` | `get_security_config_endpoint` |
| `GET /api/system/updates` | `get_system_updates` |

`GET /api/system/status`, ASUS-ROG und Freenove bleiben in `app.py`.

## Runtime

Neue Adapter in `system_runtime.py`:

- `get_cpu_temp`, `get_updates_categorized`
- `get_installed_packages_list`, `get_security_config`, `list_running_processes`
- `http_exception` (FastAPI-Wrapper)

## Tests

`backend/tests/test_app_router_slice_e11.py` — 11 Routen gesamt im System-Router.
