# APP Router Slice E.1 — Festlegung

**HEAD vorher:** `5a8a54c`  
**Slice:** 4 read-only GET-Routen  
**Ergebnis:** `safe_app_router_slice_e1` (nicht `no_safe_slice`)

## Extrahierte Routen

| Pfad | Methode | Zielmodul | Handler |
|------|---------|-----------|---------|
| `/health` | GET | `backend/api/routes/health.py` | `health_check` |
| `/api/init/status` | GET | `backend/api/routes/health.py` | `init_status` |
| `/api/logs/path` | GET | `backend/api/routes/health.py` | `logs_path` |
| `/api/version` | GET | `backend/api/routes/version.py` | `get_version` |

## Einbindung in `app.py`

```python
from api.routes.health import router as health_router
from api.routes.version import router as version_router
app.include_router(health_router)
app.include_router(version_router)
```

Kein `prefix` — öffentliche Pfade unverändert.

## Semantik

- Handler-Logik 1:1 verschoben (keine neue Businesslogik)
- `/api/version`: `app.routes` → `request.app.routes` (gleiche Snapshot-Quelle zur Laufzeit)
- Lazy-Imports aus `app` nur für `CONFIG_*`, `LOG_PATH`, `get_app_edition` (kein Zirkularimport beim Modul-Load)

## Nächster Schritt E.2

Kandidaten: `GET /api/status`, `GET /api/system/paths` (nach Prüfung von `_root_mount_device`), Settings-Read-Routen.
