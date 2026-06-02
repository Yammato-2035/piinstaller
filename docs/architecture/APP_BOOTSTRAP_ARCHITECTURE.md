# App-Bootstrap-Architektur

**Paket:** `backend/app_bootstrap/` (nicht `platform` — stdlib-Kollision)

## Verantwortlichkeiten

| Modul | Aufgabe |
|-------|---------|
| `app_factory.py` | `create_app()` — FastAPI-Instanz, Lifespan-Hooks |
| `middleware_registry.py` | `register_middlewares(app)` — CORS, Profil-Route-Block, Request-IDs |
| `router_registry.py` | Profilgated optionale Router; `register_core_routes()` Stub für Legacy |
| `startup_diagnostics.py` | `record_router_registry_result`, `get_last_startup_diagnostics()` |
| `version_router_diagnostics.py` | Felder in `GET /api/version` |

## `app.py`

Importiert `create_app`, registriert Middleware und optionale Router, behält **vorerst** Kern-Routen. Keine neue Businesslogik in Bootstrap-Modulen.

## Optionale Router

Fehler bei optionalem Import → `import_failed` in Diagnostik, **kein** Prozess-Exit. Profil `release` → `disabled_by_profile` für Dev-Dashboard und Rescue-Agent.

## Diagnose in `/api/version`

- `rescue_agent_router_status` / `rescue_agent_router_error`
- `router_registry_summary`
- `startup_diagnostics_status`
