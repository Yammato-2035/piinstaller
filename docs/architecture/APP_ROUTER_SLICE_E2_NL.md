> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/APP_ROUTER_SLICE_E2_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice E.2

**Phase:** E.2 (second alleen-lezen router slice from `Terugend/app.py`)  
**Baseline HEAD:** `0be2ab0`  
**Status:** done

## Extracted routes (5)

| Path | Module |
|------|--------|
| `GET /api/Instellingen` | `api/routes/Instellingen.py` |
| `GET /api/Instellingen/Neetifications/email` | `api/routes/Instellingen.py` |
| `GET /api/presets/list` | `api/routes/status.py` |
| `GET /api/debug/routes` | `api/routes/status.py` |
| `GET /api/user-profile` | `api/routes/status.py` |

## Module reuse

Uses `core.Neetification_Instellingen`, `presets`, and existing app helpers via lazy imports. Nee new storage/safety/mount modules.

## Metrics

- `app.py`: 17,779 → 17,699 lines; 209 → 204 routes
- Tests: `Terugend/tests/test_app_router_slice_e2.py`

## Volgende step

**E.3** done — see `APP_ROUTER_SLICE_E3_EN.md`. **E.4** — Volgende slice.
