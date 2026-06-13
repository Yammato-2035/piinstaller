# Webserver Status Facade — G.7 (EN)

**HEAD:** after G.7 · **Status:** done

## Module

`backend/core/webserver_status_facade.py` · `WEBSERVER_STATUS_FACADE_VERSION = 1`

## Public API

| Function | Purpose |
|----------|---------|
| `build_webserver_status()` | Legacy `GET /api/webserver/status` payload |
| `build_webserver_status_section()` | Section wrapper (`build_section_status`) |
| `build_webserver_frontend_section()` | `pi_installer` block |
| `build_webserver_status_diagnostics()` | Metadata |

## Delegation

| Area | Owner |
|------|-------|
| Network | `network_info_facade.build_network_info` |
| Frontend port | `network_info_facade.detect_frontend_port` |
| Services/CMS/ports | Legacy adapters → `app.*` |

## Migration

| Route | Before | After |
|-------|--------|-------|
| `GET /api/webserver/status` | Logic in `app.py` | `build_webserver_status()` |

**G.5 bypass removed:** no `_detect_frontend_port` in handler.

## Tests

- `test_webserver_status_facade_v1.py`
- `test_webserver_status_route_migration_g7.py`

## Next step

**G.6** System Info Facade **or** **G.8** Network Discovery.
