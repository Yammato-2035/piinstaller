# Deploy Evidence Router Extraction (Phase D.4)

**Module:** `backend/deploy/routes_evidence.py`  
**Status:** complete

## Extracted routes (6 POST, plan-only)

Identifier/evidence routes from C.5/C.6 using `build_plan_only_response`.

## Why keep POST?

API compatibility — clients still POST; response is plan/evidence without execution.

## allowed_to_execute

Stays **false** (C.4). No runner execution, no `runner_*` imports in the router.

## Excluded

Governance/versioning decoupled routes, direct runner calls, execute/write paths.

## Next step D.5

Governance router or further evidence slice.

## D.6 (orchestrator target)

No further extraction — thin orchestrator target documented (`DEPLOY_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`).

## D.7 (additional evidence slice)

6 more plan-only POST routes — see `DEPLOY_EVIDENCE_ROUTER_EXTRACTION_D7_EN.md`. Evidence router: 12 routes total.
