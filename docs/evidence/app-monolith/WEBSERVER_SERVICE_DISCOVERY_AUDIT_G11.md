# Webserver Service Discovery Audit — G.11

**Datum:** 2026-06-10  
**HEAD (Start):** 23462c1  
**Scope:** read-only; keine API-/Response-Änderungen

## Ist-Analyse (vor Extraktion)

| Symbol | Ort | Problem |
|--------|-----|---------|
| `_legacy_get_running_services` | `webserver_status_facade` | lazy `import app` |
| `_legacy_get_installed_apps` | `webserver_status_facade` | lazy `import app` |
| `_legacy_get_website_names` | `webserver_status_facade` | lazy `import app` |
| `_legacy_run_command` | `webserver_status_facade` | lazy `import app` |
| `_legacy_check_installed` | `webserver_status_facade` | lazy `import app` |
| `check_installed` | `app.py` ~5135 | Monolith-Implementierung |
| `get_installed_apps` | `app.py` ~5437 | Monolith-Implementierung |
| `get_running_services` | `app.py` ~5516 | `systemctl is-active` |
| `get_website_names` | `app.py` ~7798 | nginx/apache grep |

Port/Network bereits über `network_info_facade` / `network_discovery` (G.8).

## Ziel-Owner

`backend/core/webserver_service_discovery.py` — `WEBSERVER_SERVICE_DISCOVERY_VERSION = 1`

## Öffentliche API

- `discover_running_services()`
- `discover_frontend_port()` → `network_discovery.detect_frontend_port`
- `discover_webserver_stack()`
- `discover_installed_web_services()`
- `build_webserver_service_diagnostics()`

## Migration

- `webserver_status_facade`: nur Delegation an `webserver_service_discovery` (kein `import app`)
- `app.py`: dünne Wrapper für Legacy-Aufrufer

## Risiken

- `get_installed_apps` nutzt im Core vereinfachtes `run_command` (ohne sudo/PackageKit) — gleiches Verhalten wie Facade-Probes vor G.11
- Andere `app.run_command`-Aufrufer unverändert

## Tests

`test_webserver_service_discovery_v1`, `test_webserver_status_facade_v1` (angepasst)
