# app.py — Zustand nach partielle Decomposition

**Stand:** 2026-06-02

## Kennzahlen

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| Zeilen | ~17 742 | **17 686** |
| `include_router(` in `app.py` | viele (inkl. optional) | **17** (nur Kern/Legacy) |
| `@app.middleware` | >0 | **0** (→ Registry) |

## Ausgelagert

- `create_app()` → `app_bootstrap.app_factory`
- `register_middlewares()` → `app_bootstrap.middleware_registry`
- Optionale Router → `app_bootstrap.router_registry.register_all_routes()`
- Startup-Diagnostik → `app_bootstrap.startup_diagnostics`
- Version-Router-Felder → `app_bootstrap.version_router_diagnostics.inject_router_diagnostics()`
- Dev-Dashboard-Status → `core.dev_dashboard_status_service.build_dev_dashboard_status()`

## Noch in app.py (`APP_DECOMPOSITION_REMAINING`)

- Kern-API-Routen, Backup/Restore/Partitions/Deploy/Inspect-Handler
- Große Hilfs- und Businessfunktionen (historisch gewachsen)
- `register_core_routes()` in Registry ist Stub — Migration folgt inkrementell

## Bewertung

Zeilenzahl **nicht** stark gesunken; strukturelle Entkopplung an Bootstrap-Grenze **erreicht**. Weitere Reduktion erfordert routenweise Extraktion ohne API-Bruch.
