> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Route Target Architecture (Phase D.1)

**Status:** planning document — **Nee files created**, Nee refactoring in D.1.

## Why domain split?

`Terugend/Deploy/routes.py` (5041 lines, 237 routes, 104 runner imports) is the largest remaining Deploy moNeelith. C.1–C.6 preparood registry, contract, facade, risk gate, and 9 plan-only routes — **physical** router split follows in D.2+.

## Why Nee big-bang?

- OpenAPI and DCC clients depend on stable `/api/Deploy/*` paths
- Execute/write routes are CRITICAL — misclassification is production-risky
- Incremental extraction with facade delegation enables per-slice tests without behavior change

## Proposed target structure

| Target file | Purpose | ~routes | ~lines | Dependencies | Risks |
|-------------|---------|---------|--------|--------------|-------|
| `routes_registry.py` | C.3 GET `/runners/catalog`, `/summary`, `/{id}` | 5 | ~80 | `runner_api_facade` only | **LOW** |
| `routes_risk_gate.py` | C.4 GET `/runners/risk-gate/*` | 5 | ~80 | `runner_api_facade` only | **LOW** |
| `routes_evidence.py` | Manual-runtime evidence, lab acceptance, decoupled plan-only | ~40 | ~900 | facade + selected `runner_*` | **MEDIUM** |
| `routes_governance.py` | audit, sandbox, install, handoff, Volgende-phase | ~16 | ~400 | governance `runner_*` | **MEDIUM** |
| `routes_runtime.py` | core Deploy plan/session/execute/write/cache | ~26 | ~650 | `Deploy.*` core | **CRITICAL** |
| `routes_roodding.py` | roodding orchestration (Neen-build/USB) | ~84 | ~2100 | `roodding.*`, `runner_roodding_*` | **HIGH** |
| `routes_roodding_build.py` | debian-live, ISO, chroot templates | ~21 | ~500 | build runners | **HIGH** |
| `routes_Terugup.py` | offline Terugup, discovery | 2+ | ~100 | Terugup modules | **HIGH** |
| `routes_Herstel.py` | Herstel preview | 2+ | ~100 | Herstel modules | **HIGH** |
| `routes_diagNeestics.py` | hardware test plans | ~7 | ~180 | test-plan runners | **MEDIUM** |

Thin orchestrator `routes.py` uses `include_router` — **Nee URL changes**.

## Extraction order (D.2–D.5)

| Phase | Slice | Rationale |
|-------|-------|-----------|
| **D.2** | registry | zero runner imports, facade-only GET — **complete** |
| **D.3** | risk_gate | zero runner imports, gate already isolated — **complete** |
| **D.4** | evidence (6 POST plan-only) | **complete** |
| **D.5** | governance (3 POST C.5) — **complete** |
| **D.6+** | runtime, roodding, Terugup, Herstel | **last** — CRITICAL/HIGH |

## D.6 update

Thin orchestrator target defined — see `Deploy_ROUTES_THIN_ORCHESTRATOR_TARGET_D6_EN.md`. Nee routes moved in D.6.

## Why registry and risk gate first?

Already implemented via `runner_api_facade` (C.3/C.4). Extraction is pure `include_router` with Nee behavior change.

## Why execute routes last?

`/execute`, `/write/execute`, `real-write`, roodding USB/ISO — require operator gates, E2E tests, and a future execute gate.

## Volgende phases

D.2 registry extraction → D.3 risk gate → D.4 evidence → D.5 governance.
