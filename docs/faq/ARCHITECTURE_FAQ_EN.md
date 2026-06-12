# Architecture FAQ — Core Facades (EN)

Short answers on storage/mount/safety facades (Phase A.1 + caller migration A.2–A.4). No marketing copy.

## What are core facades?

Three modules under `backend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. They are the **canonical interface** for device discovery, mount plans, and write-target checks.

## Why do they exist?

The monolith audit found many duplicates (`lsblk` in `app.py`, `safe_device`, rescue, deploy runners). Facades stop each new module from reimplementing the same logic.

## What changed in A.1?

- Public contracts (types + functions)
- Documentation and inventory
- Warn-only boundary check
- Unit tests for contracts

**Not** changed: existing APIs, runtime behavior, legacy imports.

## Can I still import `safe_device` directly?

**Legacy:** yes, existing code stays. **New modules:** no — use facades only (see `CORE_FACADE_RULES_EN.md`).

## Does the mount facade execute real mounts?

No. `build_readonly_mount_plan` and validators are **plan-only** / analysis.

## Which safety contexts exist?

`live`, `rescue`, `partition_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## When does the boundary check block?

Currently **warnings only** in `check-module-boundaries.sh`. CI blocking is planned for a later phase.

## What was migrated in A.2–A.4?

`preflight/backup.py`, `backup_engine.py`, and `restore_engine.py` import safety only via `core.safety_facade`. Error codes and behavior are unchanged (delegation).

## Why is `app.py` not split immediately?

~18k lines, ~213 routes — router extraction needs its own phase B with OpenAPI parity. Engine safety migration was isolated and low risk.

## Why is the boundary guard still partly warn-only?

`app.py`, deploy runners, and storage legacy are not migrated yet. Stricter checks already apply to the three migrated safety callers.

## Does backup or restore behavior change?

**No** — same `safe_device`/`write_guard` logic, only a central import path. No new target paths, no weakened gates.

## Why is this safer?

Fewer scattered imports → less risk that new modules reimplement safety. The boundary guard detects regressions in migrated files.

## What was migrated in B.1?

blkid/storage discovery in `backup_target_auto_prepare` and `inspect/collector` goes through `storage_facade`. `partition_storage_facade` uses `safety_facade` instead of direct `write_guard`.

## What is the deploy runner registry (C.1)?

Static inventory and metadata for **115** `runner_*.py` files under `backend/deploy/`. Module: `runner_registry.py`. **No** runner execution, **no** refactoring of the runners themselves.

## What is the runner result contract (C.2)?

Unified result schema (`RunnerResult`) with 6 status values, `warnings`/`errors`, `evidence_paths`, and `no_execution_performed`. Module: `runner_result_contract.py`. Legacy dicts map via `normalize_legacy_runner_result` — runners themselves unchanged.

## Why are runners not refactored immediately?

Largest risk cluster (~37k lines). C.1 + C.2 provide metadata and the result contract. C.3–C.5: API facade, risk gate, incremental migration.

## What is the deploy runner API facade (C.3)?

Read-only layer `runner_api_facade.py` + **5 GET routes** under `/api/deploy/runners/*`. Lists registry/contract — **no** runner execution. The 112 direct runner imports in `routes.py` remain for now.

## What is the deploy runner risk gate (C.4)?

`runner_risk_gate.py` evaluates `risk_level`, `execution_policy`, and optional operator context. **`allowed_to_execute` stays false** — planning decisions only, for C.5.

## What was decoupled in C.5/C.6?

**C.5:** 4 routes (version/identifier/next-phase). **C.6:** 5 evidence/identifier routes. **113→104** imports. `facade_decoupling_c5/c6`, execute still false.

## What is phase D.1 (route domain audit)?

Full domain analysis of `backend/deploy/routes.py` (**5041 lines, 237 routes**) with no refactoring. Deliverables: inventory, domain matrix, target architecture, extraction risk. **No** routers moved, **no** API changes.

## Why domain split instead of big-bang?

OpenAPI/DCC stability; CRITICAL execute routes last. Incremental: registry → risk gate → evidence → governance → runtime/rescue.

## Why extract registry/risk gate first (D.2/D.3)?

Both use only `runner_api_facade` — **zero** direct `runner_*` imports in handlers. Lowest risk.

## Why execute routes last?

`/execute`, `/write/execute`, `real-write` are **CRITICAL** — need operator gates and E2E before physical extraction.

## What is phase D.2 (registry router)?

5 GET routes moved to `routes_registry.py`. Paths unchanged, facade only, no runner execution.

## What is phase D.3 (risk-gate router)?

5 GET routes moved to `routes_risk_gate.py`. Facade only, `allowed_to_execute` stays false.

## What is phase D.4 (evidence router)?

6 POST plan-only routes moved to `routes_evidence.py`. POST unchanged, `build_plan_only_response`, no runner execution.

## What is phase D.5 (governance router)?

3 C.5 routes moved to `routes_governance.py`. All 9 decoupled routes now in sub-routers.

## What is phase D.6 (thin orchestrator)?

No routes moved. Inventory, ownership matrix, target (<500 lines, 0 runner imports), D.7+ sequence, extended boundary guard.

## What is Phase D.7 (evidence slice)?

6 additional plan-only POST routes from `routes.py` to `routes_evidence.py` (12 total). No rescue/execute/write paths. `routes.py`: 4671 lines, 99 runner imports.

## What is the module catalog?

Binding inventory at `docs/architecture/MODULE_CATALOG_EN.md` with function ownership matrix and do-not-duplicate rules. Cursor must check for CANONICAL modules before new code.

## What is D.11 (runtime router)?

Eight read-only/status POST routes in `routes_runtime.py`. `routes.py`: 4324→4120 lines, 89→81 runner imports.

## What is E.1 (app.py router slice)?

Four read-only GET routes extracted to `api/routes/health.py` and `version.py`. `app.py`: 17,857→17,779 lines. See `docs/architecture/APP_ROUTER_SLICE_E1_EN.md`.

## What is E.2 (app.py router slice)?

Five read-only GET routes in `api/routes/settings.py` and `status.py`. `app.py`: 17,779→17,699 lines.

## What is E.3 (app.py router slice)?

Five read-only GET routes (logs/tail, self-update/status, apps, DCC capability gates). `app.py`: 17,699→17,617 lines.

## What is E.4 (app.py router slice)?

Five DCC index GET routes in `dev_dashboard_readonly.py` using only `core.dev_dashboard*`. `app.py`: 17,617→17,568 lines.

## What is E.5 (roadmap router slice)?

Five roadmap registry GET routes in `dev_dashboard_roadmap.py` via `load_roadmap_registry_bundle` only.

## What is E.6 (roadmap next-prompts)?

Two GET routes moved to `dev_dashboard_roadmap.py`. `app.py`: 17,499→17,472 lines.

## What is E.7 (router slice candidate audit)?

Re-scan of all **187** remaining `@app.*` routes — **no extraction**. Result: **3** safe E.8 candidates (backend-health, notifications/status/events); blocked facades for status/network/DCC. See `docs/architecture/APP_ROUTER_SLICE_CANDIDATE_AUDIT_E7_EN.md`.

## Next step?

**E.8** — extract 3 DCC read-only GETs **or** facade phase F.1 (system/DCC status).

## Further reading

- `docs/architecture/MODULE_CATALOG_EN.md`
- `docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md`
- `docs/architecture/DO_NOT_DUPLICATE_RULES_EN.md`
- `docs/knowledge-base/architecture/CORE_FACADES_EN.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`
- `docs/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`
- `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`
- `docs/architecture/DEPLOY_RUNNER_API_FACADE_EN.md`
- `docs/architecture/DEPLOY_RUNNER_RISK_GATE_EN.md`
- `docs/architecture/DEPLOY_RUNNER_ROUTES_DECOUPLING_C5_EN.md`
- `docs/architecture/DEPLOY_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`
