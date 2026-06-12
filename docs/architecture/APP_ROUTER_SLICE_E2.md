# APP Router Slice E.2

**Phase:** E.2 (zweiter read-only Router-Slice aus `backend/app.py`)  
**Baseline HEAD:** `0be2ab0`  
**Status:** erledigt

## Extrahierte Routen (5)

| Pfad | Modul |
|------|-------|
| `GET /api/settings` | `api/routes/settings.py` |
| `GET /api/settings/notifications/email` | `api/routes/settings.py` |
| `GET /api/presets/list` | `api/routes/status.py` |
| `GET /api/debug/routes` | `api/routes/status.py` |
| `GET /api/user-profile` | `api/routes/status.py` |

## Module-Reuse

| Domäne | Canonical |
|--------|-----------|
| Notification settings | `core.notification_settings` |
| Presets | `presets.list_presets` |
| Version (debug) | `core.versioning` via `get_pi_installer_version` |
| User profile | bestehende `app`-Hilfsfunktionen (lazy import) |

Keine Storage-/Safety-/Mount-Parallelmodule.

## Metriken

- `app.py`: 17.779 → 17.699 Zeilen; 209 → 204 Routen
- Tests: `backend/tests/test_app_router_slice_e2.py`

## Nächster Schritt

**E.3** — weitere read-only Routen ohne subprocess.

## Evidence

`docs/evidence/app-monolith/APP_ROUTER_SLICE_E2.md`
