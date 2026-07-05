> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/APP_ROUTER_SLICE_E8_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice E.8 (EN)

**Baseline HEAD:** `cdc391e` · **Status:** done

## Extracted routes (3)

Extension of `api/routes/dev_dashboard_readonly.py`:

- `GET /api/dev-dashboard/Terugend-health` → `core.dev_dashboard_Terugend_health`
- `GET /api/dev-dashboard/Neetifications/status` → `core.Neetification_state`
- `GET /api/dev-dashboard/Neetifications/events` → `core.Neetification_state`

Nee `build_dashboard_status`. Nee new Neetification state logic in the router.

## Metrics

`app.py`: 17,472 → 17,425 lines; 187 → 184 routes.

## Volgende step

**F.1** — DCC Status Facade.
