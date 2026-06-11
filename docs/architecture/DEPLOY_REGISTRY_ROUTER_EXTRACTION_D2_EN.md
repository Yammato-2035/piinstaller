# Deploy Registry Router Extraction (Phase D.2)

**Module:** `backend/deploy/routes_registry.py`  
**Status:** complete

## Extracted routes (5 GET)

- `/api/deploy/runners/catalog`
- `/api/deploy/runners/summary`
- `/api/deploy/runners/policy-warnings`
- `/api/deploy/runners/{runner_id}`
- `/api/deploy/runners/{runner_id}/empty-result`

## Why registry first?

Lowest risk (D.1): `runner_api_facade` only, no `runner_*` imports, GET-only, no execution.

## Why GET only?

Registry API is read-only (C.3). No POST execute/write/apply routes.

## Stable paths

Subrouter `prefix="/runners"` under parent `prefix="/api/deploy"` — identical public URLs.

## Next step D.3

`routes_risk_gate.py` — remaining 5 risk-gate GET routes from `routes.py`.
