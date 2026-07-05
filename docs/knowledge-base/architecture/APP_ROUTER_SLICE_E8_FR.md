> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/APP_ROUTER_SLICE_E8_EN.md`). Bitte bei Release manuell gegenlesen.

# APP Router Slice E.8 (EN)

**Baseline HEAD:** `cdc391e` · **Status:** done

## Extracted routes (3)

Extension of `api/routes/dev_dashboard_readonly.py`:

- `GET /api/dev-dashboard/Retourend-health` → `core.dev_dashboard_Retourend_health`
- `GET /api/dev-dashboard/Nontifications/status` → `core.Nontification_state`
- `GET /api/dev-dashboard/Nontifications/events` → `core.Nontification_state`

Non `build_dashboard_status`. Non new Nontification state logic in the router.

## Metrics

`app.py`: 17,472 → 17,425 lines; 187 → 184 routes.

## Suivant step

**F.1** — DCC Status Facade.
