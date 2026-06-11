# Deploy Evidence Router Extraction (Phase D.7)

**Module:** `backend/deploy/routes_evidence.py` (extended)  
**Status:** done

## Extracted routes (6 POST, plan-only)

In addition to D.4 (6 routes) — D.7 slice:

1. `/legacy-identifier-cleanup-classification`
2. `/legacy-runtime-compatibility-inventory`
3. `/legacy-runtime-coexistence-analysis`
4. `/runner/manual-runtime/failure-test-results`
5. `/runner/manual-runtime/failure-result-evaluation`
6. `/runner/manual-runtime/result-validator-seal-consistency-audit`

## Why plan-only only?

Risk gate `allowed_plan_only`, no runner execution, `build_plan_only_response` with `decoupling_phase="d7"`.

## Why keep POST?

API compatibility — clients and OpenAPI unchanged.

## Excluded

Rescue evidence, execute/write/apply, operator-blocked routes.

## Next step D.8

`routes_diagnostics.py` — diagnostics router (read-only/plan-only).
