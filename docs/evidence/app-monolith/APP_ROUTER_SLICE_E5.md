# APP Router Slice E.5 — Festlegung

**HEAD vorher:** `7795212`  
**Ergebnis:** `safe_app_router_slice_e5` (5 Routen)

## Modul

`backend/api/routes/dev_dashboard_roadmap.py`

## Extrahierte Routen

Alle nutzen ausschließlich `core.dev_dashboard_roadmap.load_roadmap_registry_bundle()`.

## In app.py verbleibend

- `GET /api/dev-dashboard/roadmap` (mit `build_dashboard_status`)
- `GET /api/dev-dashboard/roadmap/next-prompts`
- `GET /api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}`

## Nächster Schritt E.6

`next-prompts`, `export-next-prompt` — weiterhin nur Core-Roadmap-Funktionen.
