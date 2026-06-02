# Modul-Grenzen (Setuphelfer Backend)

## Erlaubt in `app.py`

- `app = create_app(...)`
- Aufruf `register_middlewares`, `register_all_routes`
- Legacy-Kern-Routen bis Phase B abgeschlossen

## Verboten in `app.py` (Ziel)

- Deploy-Drift-Berechnung
- Dev-Dashboard-Aggregation (→ `core.dev_dashboard_status_service`)
- Rescue-Agent-Fachlogik (→ `rescue_agent/`)
- Direkte Safety-/Mount-Ausführung (→ Facades)

## Rescue / Rettungsstick

- Storage: `core.storage_facade`
- Mount: `core.mount_facade`
- Safety: `core.safety_facade` → `safety.write_guard`

## Prüfung

`scripts/check-module-boundaries.sh` — JSON-Status `ok` | `review_required` | `blocked`
