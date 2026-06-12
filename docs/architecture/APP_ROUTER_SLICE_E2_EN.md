# APP Router Slice E.2

**Phase:** E.2 (second read-only router slice from `backend/app.py`)  
**Baseline HEAD:** `0be2ab0`  
**Status:** done

## Extracted routes (5)

| Path | Module |
|------|--------|
| `GET /api/settings` | `api/routes/settings.py` |
| `GET /api/settings/notifications/email` | `api/routes/settings.py` |
| `GET /api/presets/list` | `api/routes/status.py` |
| `GET /api/debug/routes` | `api/routes/status.py` |
| `GET /api/user-profile` | `api/routes/status.py` |

## Module reuse

Uses `core.notification_settings`, `presets`, and existing app helpers via lazy imports. No new storage/safety/mount modules.

## Metrics

- `app.py`: 17,779 → 17,699 lines; 209 → 204 routes
- Tests: `backend/tests/test_app_router_slice_e2.py`

## Next step

**E.3** done — see `APP_ROUTER_SLICE_E3_EN.md`. **E.4** — next slice.
