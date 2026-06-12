# APP Router Slice E.2 — Festlegung

**HEAD vorher:** `0be2ab0`  
**Slice:** 5 read-only GET-Routen  
**Ergebnis:** `safe_app_router_slice_e2`

## Extrahierte Routen

| Pfad | Methode | Zielmodul | Handler |
|------|---------|-----------|---------|
| `/api/settings` | GET | `backend/api/routes/settings.py` | `get_settings` |
| `/api/settings/notifications/email` | GET | `backend/api/routes/settings.py` | `get_notification_email_settings` |
| `/api/presets/list` | GET | `backend/api/routes/status.py` | `api_list_presets` |
| `/api/debug/routes` | GET | `backend/api/routes/status.py` | `debug_routes` |
| `/api/user-profile` | GET | `backend/api/routes/status.py` | `get_user_profile` |

## Einbindung in `app.py`

```python
app.include_router(settings_router)
app.include_router(status_router)
```

Kein `prefix` — öffentliche Pfade unverändert.

## Semantik

- Handler 1:1 verschoben
- `/api/debug/routes`: `app.routes` → `request.app.routes`
- POST/PUT Handler (`set_settings`, `update_user_profile`, …) bleiben in `app.py`

## Nächster Schritt E.3

Kandidaten nach Prüfung: `GET /api/system/network` (nur Demo-Mode-Pfad?), weitere Settings-GET, einfache Status-Endpunkte ohne subprocess.
