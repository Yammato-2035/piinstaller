# Deploy Routes Thin Orchestrator — Target (Phase D.6)

**Status:** target definition — **no refactoring in D.6**

## Current state (after D.2–D.5)

`backend/deploy/routes.py` is **orchestrator + legacy monolith**:

- 4× `include_router(...)` for registry, risk gate, evidence, governance
- 4821 lines, 218 direct routes, 103 runner imports
- execute/rescue/write paths remain here

## Target

Long-term `routes.py` should **only**:

1. Create `APIRouter(prefix="/api/deploy")`
2. Import sub-routers and call `include_router`
3. Optional few legacy compatibility anchors (0–10 routes)
4. **No** direct `runner_*.py` imports
5. **No** business logic / runner execution

## D.7 update (done)

6 additional plan-only POST routes in `routes_evidence.py` (12 total). `routes.py`: 4671 lines, 99 imports.

## Target metrics

| Metric | Current (D.7) | Target |
|--------|--------------:|-------:|
| `routes.py` lines | 4671 | **< 500** |
| direct runner imports | 99 | **0** |
| routes directly in routes.py | 218 | **0–10** legacy |
| sub-routers | 4 | **10–14** |
| execute routes without risk gate | open | **0** (after execute gate) |

## Why guard instead of blind migration?

D.2–D.5 extracted safe facade routes. Further moves without guard risk API drift and execute leaks. D.6 introduces **measurement + ownership + D.7+ sequence**.

See `DEPLOY_ROUTE_EXTRACTION_SEQUENCE_D7_PLUS_EN.md`.
