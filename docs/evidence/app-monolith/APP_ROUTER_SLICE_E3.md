# APP Router Slice E.3 — Festlegung

**HEAD vorher:** `b667785`  
**Slice:** 5 read-only GET-Routen  
**Ergebnis:** `safe_app_router_slice_e3`

## Extrahierte Routen

| Pfad | Modul |
|------|-------|
| `GET /api/logs/tail` | `health.py` (erweitert) |
| `GET /api/self-update/status` | `status.py` (erweitert) |
| `GET /api/apps` | `catalog.py` (neu) |
| `GET /api/dev-dashboard/capability-status` | `capabilities.py` (neu) |
| `GET /api/dev-dashboard/compact-status` | `capabilities.py` (neu) |

## Nächster Schritt E.4

Weitere read-only GET ohne subprocess — z. B. `dev-dashboard/modules`, `evidence-index` (nur Dateiscans).
