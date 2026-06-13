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

Re-scan of all **187** remaining `@app.*` routes — **no extraction**. Result: **3** safe E.8 candidates.

## What is E.8 (DCC read-only router slice)?

Three GET routes moved to `dev_dashboard_readonly.py`: backend-health, notifications/status, notifications/events. Uses `core.dev_dashboard_backend_health` and `core.notification_state` only. `app.py`: 17,472→17,425 lines.

## What is F.1 (DCC Status Facade)?

Canonical module `core/dcc_status_facade.py` — read-only aggregation contract for DCC sections. **No route migration** in F.1. See `docs/architecture/DCC_STATUS_FACADE_F1_EN.md`.

## What is F.2 (DCC router migration)?

Six aggregation GET routes in `app.py` delegate to `dcc_status_facade`. No API changes. See `docs/architecture/DCC_STATUS_ROUTER_MIGRATION_F2_EN.md`.

## What is F.3 (DCC aggregation audit)?

Analysis only (no refactoring): remaining direct access, traffic-light duplicates, roadmap subrouter boundary, ai_prompt stub → facade in F.4, deploy/core coupling. See `docs/architecture/DCC_AGGREGATION_AUDIT_F3_EN.md`.

## What is F.4 (DCC delegation cleanup)?

`ai_prompt_generate_stub` and readonly router endpoints delegate to `dcc_status_facade` API helpers. No API changes. See `docs/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`.

## What is G.1 (System Status Facade)?

Canonical module `core/system_status_facade.py` — read-only aggregation for system ampel, backend runtime, installation, profile. **No route migration** in G.1. No network diagnostics. See `docs/architecture/SYSTEM_STATUS_FACADE_G1_EN.md`.

## What is G.1b (system status route migration)?

`GET /api/system/status` in `app.py` delegates to `build_system_status()`. No API changes. See `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B_EN.md`.

## What is G.2 (Network Info Facade)?

Canonical module `core/network_info_facade.py` — read-only network info, demo fallback, legacy normalization. **No route migration** in G.2. Doc: `docs/architecture/NETWORK_INFO_FACADE_G2_EN.md`.

## What is G.2b (Network Route Migration)?

`GET /api/status` (network block) and `GET /api/system/network` delegate to `network_info_facade`. No API/response change. Doc: `docs/architecture/NETWORK_INFO_ROUTE_MIGRATION_G2B_EN.md`.

## What is G.3 (Network Core Cleanup)?

`get_system_info` and `webserver_status` delegate to `network_info_facade`. Legacy `get_network_info`/`_demo_network` remain implementation behind facade adapters. Doc: `docs/architecture/NETWORK_INFO_CORE_CLEANUP_G3_EN.md`.

## What is G.4 (Network Handler Extraction)?

`GET /api/status` and `GET /api/system/network` in `api/routes/network.py`; facade delegation only. Blocked: `system-info`, `webserver/status`. Doc: `docs/architecture/NETWORK_HANDLER_EXTRACTION_G4_EN.md`.

## What is G.5 (Network Legacy Elimination Audit)?

Full inventory — **no refactoring**. 3 legacy functions in `app.py`; 1 facade bypass in `webserver_status`. Next candidates: G.6/G.7/G.8. Doc: `docs/architecture/NETWORK_NEXT_FACADE_CANDIDATES_G5_EN.md`.

## What is G.6 (System Info Facade)?

`GET /api/system-info` fully delegates to `system_info_facade`; network only via `network_info_facade`; status sections via `dcc_status_facade`. ~240 lines extracted from `app.py`. Doc: `docs/architecture/SYSTEM_INFO_FACADE_G6_EN.md`.

## What is G.7 (Webserver Status Facade)?

`GET /api/webserver/status` delegates to `webserver_status_facade`; network and port via `network_info_facade`. G.5 bypass removed. Doc: `docs/architecture/WEBSERVER_STATUS_FACADE_G7_EN.md`.

## What is G.8 (Network Discovery Core)?

Discovery logic moved from `app.py` to `network_discovery.py`; `network_info_facade` has no lazy `import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/NETWORK_DISCOVERY_CORE_G8_EN.md`.

## What is H.1 (Frontend Status ViewModel)?

Canonical module `frontend/src/viewmodels/statusViewModel.ts` — central status normalization. **No component migration** in H.1. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1_EN.md`.

## What is H.2 (Frontend Status Utility Migration)?

`trafficLightModel`, `deployDriftTone`, and `toneClass` delegate to `statusViewModel`. No UI/color change. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md`.

## What is H.3 (Frontend Status Component Migration)?

3 small DCC components delegate tone mapping to `dashboardLegacyToneFromInput`. No UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md`.

## What is H.4 (Frontend Status Component Migration — second slice)?

3 more small components (`ReadyStableSection`, `StatusCard`, `RiskWarningCard`) delegate to `isDashboardGreenStatus`, `isGreenDashboardTone`/`dashboardToneFromInput`, `riskWarningTitleKeyForLevel`. No UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`.

## What is H.5 (Frontend Status Utility Migration)?

3 small DCC utilities (`governanceMatrix`, `roadmapFilter`, `buildGovernancePrompt`) delegate status mapping to `statusViewModel`. No UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5_EN.md`.

## What is H.6 (Frontend Status Presentation Migration)?

5 presentation/utility files delegate to `statusViewModel` (LampDot, panda traffic light, governance history, standalone dashboard). No UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H6_EN.md`.

## What is H.7 (Frontend Status — final slice)?

5 presentation libs delegate to `statusViewModel`. Remaining: 10 (domain + large-page). **No H.8.** Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7_EN.md`.

## What is G.9 (Hardware Discovery Core)?

Hardware/system discovery extracted from `app.py` to `hardware_discovery.py`; `system_info_facade` has no `_legacy_*`/`import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/HARDWARE_DISCOVERY_CORE_G9_EN.md`.

## What is G.11 (Webserver Service Discovery)?

Webserver/service/CMS discovery in `webserver_service_discovery.py`; `webserver_status_facade` without `import app`. Legacy wrappers in `app.py`. Doc: `docs/architecture/WEBSERVER_SERVICE_DISCOVERY_G11_EN.md`.

## What is G.12 (System Status Core)?

Ampel logic (backup/restore/security/updates) in `system_status_core.py`; facade delegates only. Security/update adapters stay in core. Doc: `docs/architecture/SYSTEM_STATUS_CORE_G12_EN.md`.

## What is P.1 (Storage Discovery Canonical)?

Canonical lsblk/findmnt/blkid owner `storage_discovery.py`; `storage_facade` delegates. `app.py` storage blocks intentionally deferred. Matrix: `docs/architecture/STORAGE_DISCOVERY_OWNERSHIP_MATRIX.md`.

## What is D.12 (Deploy Thin-Orchestrator Audit)?

Audit of `deploy/routes.py` (190 routes, 81 runner imports); final plan without execute extraction. Doc: `docs/architecture/DEPLOY_THIN_ORCHESTRATOR_FINAL_PLAN.md`.

## Next step?

G.13 (remaining `system_status_facade`→app sections) · P.2 (`app.py` storage migration) · D.13 (rescue domain router).

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
