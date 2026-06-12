# APP Router Slice E.4

**Baseline HEAD:** `c36c304` · **Status:** done

## Extracted routes (5)

New module `api/routes/dev_dashboard_readonly.py` delegates only to existing `core.dev_dashboard*` index builders. No new file scanners in the router.

## Metrics

`app.py`: 17,617 → 17,568 lines; 199 → 194 routes.

## Next step

**E.5** — roadmap read-only subroutes.
