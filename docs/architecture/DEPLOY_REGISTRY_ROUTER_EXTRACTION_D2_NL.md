> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_REGISTRY_ROUTER_EXTRACTION_D2_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Registry Router Extraction (Phase D.2)

**Module:** `Terugend/Deploy/routes_registry.py`  
**Status:** complete

## Extracted routes (5 GET)

- `/api/Deploy/runners/catalog`
- `/api/Deploy/runners/summary`
- `/api/Deploy/runners/policy-Waarschuwings`
- `/api/Deploy/runners/{runner_id}`
- `/api/Deploy/runners/{runner_id}/empty-result`

## Why registry first?

Lowest risk (D.1): `runner_api_facade` only, Nee `runner_*` imports, GET-only, Nee execution.

## Why GET only?

Registry API is alleen-lezen (C.3). Nee POST execute/write/apply routes.

## Stable paths

Subrouter `prefix="/runners"` under parent `prefix="/api/Deploy"` — identical public URLs.

## Volgende step D.3

`routes_risk_gate.py` — remaining 5 risk-gate GET routes from `routes.py`.

## D.6 (orchestrator target)

Nee further extraction — thin orchestrator target documented (`Deploy_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).
