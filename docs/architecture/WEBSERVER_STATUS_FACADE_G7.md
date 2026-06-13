# Webserver Status Facade — G.7

**HEAD:** nach G.7 · **Status:** erledigt

## Modul

`backend/core/webserver_status_facade.py` · `WEBSERVER_STATUS_FACADE_VERSION = 1`

## Öffentliche API

| Funktion | Zweck |
|----------|-------|
| `build_webserver_status()` | Legacy `GET /api/webserver/status` Payload |
| `build_webserver_status_section()` | Section-Wrapper (`build_section_status`) |
| `build_webserver_frontend_section()` | `pi_installer` Block |
| `build_webserver_status_diagnostics()` | Metadaten |

## Delegation

| Bereich | Owner |
|---------|-------|
| Network | `network_info_facade.build_network_info` |
| Frontend-Port | `network_info_facade.detect_frontend_port` |
| Services/CMS/Ports | Legacy-Adapter → `app.*` |

## Migration

| Route | Vorher | Nachher |
|-------|--------|---------|
| `GET /api/webserver/status` | Logik in `app.py` | `build_webserver_status()` |

**G.5-Bypass beseitigt:** kein `_detect_frontend_port` mehr im Handler.

## Tests

- `test_webserver_status_facade_v1.py`
- `test_webserver_status_route_migration_g7.py`

## Nächster Schritt

**G.6** System Info Facade **oder** **G.8** Network Discovery.
