# Deploy Route Target Architecture (Phase D.1)

**Status:** planning document — **no files created**, no refactoring in D.1.

## Why domain split?

`backend/deploy/routes.py` (5041 lines, 237 routes, 104 runner imports) is the largest remaining deploy monolith. C.1–C.6 prepared registry, contract, facade, risk gate, and 9 plan-only routes — **physical** router split follows in D.2+.

## Why no big-bang?

- OpenAPI and DCC clients depend on stable `/api/deploy/*` paths
- Execute/write routes are CRITICAL — misclassification is production-risky
- Incremental extraction with facade delegation enables per-slice tests without behavior change

## Proposed target structure

| Target file | Purpose | ~routes | ~lines | Dependencies | Risks |
|-------------|---------|---------|--------|--------------|-------|
| `routes_registry.py` | C.3 GET `/runners/catalog`, `/summary`, `/{id}` | 5 | ~80 | `runner_api_facade` only | **LOW** |
| `routes_risk_gate.py` | C.4 GET `/runners/risk-gate/*` | 5 | ~80 | `runner_api_facade` only | **LOW** |
| `routes_evidence.py` | Manual-runtime evidence, lab acceptance, decoupled plan-only | ~40 | ~900 | facade + selected `runner_*` | **MEDIUM** |
| `routes_governance.py` | audit, sandbox, install, handoff, next-phase | ~16 | ~400 | governance `runner_*` | **MEDIUM** |
| `routes_runtime.py` | core deploy plan/session/execute/write/cache | ~26 | ~650 | `deploy.*` core | **CRITICAL** |
| `routes_rescue.py` | rescue orchestration (non-build/USB) | ~84 | ~2100 | `rescue.*`, `runner_rescue_*` | **HIGH** |
| `routes_rescue_build.py` | debian-live, ISO, chroot templates | ~21 | ~500 | build runners | **HIGH** |
| `routes_backup.py` | offline backup, discovery | 2+ | ~100 | backup modules | **HIGH** |
| `routes_restore.py` | restore preview | 2+ | ~100 | restore modules | **HIGH** |
| `routes_diagnostics.py` | hardware test plans | ~7 | ~180 | test-plan runners | **MEDIUM** |

Thin orchestrator `routes.py` uses `include_router` — **no URL changes**.

## Extraction order (D.2–D.5)

| Phase | Slice | Rationale |
|-------|-------|-----------|
| **D.2** | registry | zero runner imports, facade-only GET — **complete** |
| **D.3** | risk_gate | zero runner imports, gate already isolated — **complete** |
| **D.4** | evidence (6 POST plan-only) | **complete** |
| **D.5** | governance | audit/sandbox without device-write |
| **D.6+** | runtime, rescue, backup, restore | **last** — CRITICAL/HIGH |

## Why registry and risk gate first?

Already implemented via `runner_api_facade` (C.3/C.4). Extraction is pure `include_router` with no behavior change.

## Why execute routes last?

`/execute`, `/write/execute`, `real-write`, rescue USB/ISO — require operator gates, E2E tests, and a future execute gate.

## Next phases

D.2 registry extraction → D.3 risk gate → D.4 evidence → D.5 governance.
