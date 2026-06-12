# APP Router Slice E.3

**Baseline HEAD:** `b667785` · **Status:** erledigt

## Extrahierte Routen (5)

| Pfad | Modul |
|------|-------|
| `GET /api/logs/tail` | `health.py` |
| `GET /api/self-update/status` | `status.py` |
| `GET /api/apps` | `catalog.py` |
| `GET /api/dev-dashboard/capability-status` | `capabilities.py` |
| `GET /api/dev-dashboard/compact-status` | `capabilities.py` |

## Module-Reuse

`core.developer_capability`, `core.dev_dashboard_compact_status`, `core.install_paths` — keine Storage-/Safety-/Mount-Duplikate.

## Metriken

`app.py`: 17.699 → 17.617 Zeilen; 204 → 199 Routen.

## Nächster Schritt

**E.4** — weitere file-based read-only GET (z. B. DCC modules/evidence-index).
