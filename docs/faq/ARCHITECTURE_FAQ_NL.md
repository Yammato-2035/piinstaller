> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/ARCHITECTURE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# Architecture FAQ — Core Facades (EN)

Short answers on storage/mount/safety facades (Phase A.1 + caller migration A.2–A.4). Nee marketing copy.

## What are core facades?

Three modules under `Terugend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. They are the **caNeenical interface** for Apparaat discovery, mount plans, and write-target checks.

## Why do they exist?

The moNeelith audit found many duplicates (`lsblk` in `app.py`, `safe_Apparaat`, roodding, Deploy runners). Facades stop each new module from reimplementing the same logic.

## What changed in A.1?

- Public contracts (types + functions)
- Documentatie and inventory
- Warn-only boundary check
- Unit tests for contracts

**Neet** changed: existing APIs, runtime behavior, legacy imports.

## Can I still import `safe_Apparaat` directly?

**Legacy:** Ja, existing code stays. **New modules:** Nee — use facades only (see `CORE_FACADE_RULES_EN.md`).

## Does the mount facade execute real mounts?

Nee. `build_readonly_mount_plan` and validators are **plan-only** / analysis.

## Which safety contexts exist?

`live`, `roodding`, `Partitie_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## When does the boundary check block?

Currently **Waarschuwings only** in `check-module-boundaries.sh`. CI blocking is planned for a later phase.

## What was migrated in A.2–A.4?

`preflight/Terugup.py`, `Terugup_engine.py`, and `Herstel_engine.py` import safety only via `core.safety_facade`. Fout codes and behavior are unchanged (delegation).

## Why is `app.py` Neet split immediately?

~18k lines, ~213 routes — router extraction needs its own phase B with OpenAPI parity. Engine safety migration was isolated and low risk.

## Why is the boundary guard still partly warn-only?

`app.py`, Deploy runners, and storage legacy are Neet migrated yet. Stricter checks already apply to the three migrated safety callers.

## Does Terugup or Herstel behavior change?

**Nee** — same `safe_Apparaat`/`write_guard` logic, only a central import path. Nee new target paths, Nee weakened gates.

## Why is this safer?

Fewer scatterood imports → less risk that new modules reimplement safety. The boundary guard detects regressions in migrated files.

## What was migrated in B.1?

blkid/storage discovery in `Terugup_target_auto_prepare` and `inspect/collector` goes through `storage_facade`. `Partitie_storage_facade` uses `safety_facade` instead of direct `write_guard`.

## What is the Deploy runner registry (C.1)?

Static inventory and metadata for **115** `runner_*.py` files under `Terugend/Deploy/`. Module: `runner_registry.py`. **Nee** runner execution, **Nee** refactoring of the runners themselves.

## What is the runner result contract (C.2)?

Unified result schema (`RunnerResult`) with 6 status values, `Waarschuwings`/`Fouts`, `evidence_paths`, and `Nee_execution_performed`. Module: `runner_result_contract.py`. Legacy dicts map via `Neermalize_legacy_runner_result` — runners themselves unchanged.

## Why are runners Neet refactorood immediately?

Largest risk cluster (~37k lines). C.1 + C.2 provide metadata and the result contract. C.3–C.5: API facade, risk gate, incremental migration.

## What is the Deploy runner API facade (C.3)?

alleen-lezen layer `runner_api_facade.py` + **5 GET routes** under `/api/Deploy/runners/*`. Lists registry/contract — **Nee** runner execution. The 112 direct runner imports in `routes.py` remain for Neew.

## What is the Deploy runner risk gate (C.4)?

`runner_risk_gate.py` evaluates `risk_level`, `execution_policy`, and optional operator context. **`allowed_to_execute` stays false** — planning decisions only, for C.5.

## What was decoupled in C.5/C.6?

**C.5:** 4 routes (version/identifier/Volgende-phase). **C.6:** 5 evidence/identifier routes. **113→104** imports. `facade_decoupling_c5/c6`, execute still false.

## What is phase D.1 (route domain audit)?

Full domain analysis of `Terugend/Deploy/routes.py` (**5041 lines, 237 routes**) with Nee refactoring. Deliverables: inventory, domain matrix, target architecture, extraction risk. **Nee** routers moved, **Nee** API changes.

## Why domain split instead of big-bang?

OpenAPI/DCC stability; CRITICAL execute routes last. Incremental: registry → risk gate → evidence → governance → runtime/roodding.

## Why extract registry/risk gate first (D.2/D.3)?

Both use only `runner_api_facade` — **zero** direct `runner_*` imports in handlers. Lowest risk.

## Why execute routes last?

`/execute`, `/write/execute`, `real-write` are **CRITICAL** — need operator gates and E2E before physical extraction.

## What is phase D.2 (registry router)?

5 GET routes moved to `routes_registry.py`. Paths unchanged, facade only, Nee runner execution.

## What is phase D.3 (risk-gate router)?

5 GET routes moved to `routes_risk_gate.py`. Facade only, `allowed_to_execute` stays false.

## What is phase D.4 (evidence router)?

6 POST plan-only routes moved to `routes_evidence.py`. POST unchanged, `build_plan_only_response`, Nee runner execution.

## What is phase D.5 (governance router)?

3 C.5 routes moved to `routes_governance.py`. All 9 decoupled routes Neew in sub-routers.

## What is phase D.6 (thin orchestrator)?

Nee routes moved. Inventory, ownership matrix, target (<500 lines, 0 runner imports), D.7+ sequence, extended boundary guard.

## What is Phase D.7 (evidence slice)?

6 additional plan-only POST routes from `routes.py` to `routes_evidence.py` (12 total). Nee roodding/execute/write paths. `routes.py`: 4671 lines, 99 runner imports.

## What is the module catalog?

Binding inventory at `docs/architecture/MODULE_CATALOG_EN.md` with function ownership matrix and do-Neet-duplicate rules. Cursor must check for CANeeNICAL modules before new code.

## What is D.11 (runtime router)?

Eight alleen-lezen/status POST routes in `routes_runtime.py`. `routes.py`: 4324→4120 lines, 89→81 runner imports.

## What is E.1 (app.py router slice)?

Four alleen-lezen GET routes extracted to `api/routes/health.py` and `version.py`. `app.py`: 17,857→17,779 lines. See `docs/architecture/APP_ROUTER_SLICE_E1_EN.md`.

## What is E.2 (app.py router slice)?

Five alleen-lezen GET routes in `api/routes/Instellingen.py` and `status.py`. `app.py`: 17,779→17,699 lines.

## What is E.3 (app.py router slice)?

Five alleen-lezen GET routes (logs/tail, self-update/status, apps, DCC capability gates). `app.py`: 17,699→17,617 lines.

## What is E.4 (app.py router slice)?

Five DCC index GET routes in `dev_dashboard_readonly.py` using only `core.dev_dashboard*`. `app.py`: 17,617→17,568 lines.

## What is E.5 (roadmap router slice)?

Five roadmap registry GET routes in `dev_dashboard_roadmap.py` via `load_roadmap_registry_bundle` only.

## What is E.6 (roadmap Volgende-prompts)?

Two GET routes moved to `dev_dashboard_roadmap.py`. `app.py`: 17,499→17,472 lines.

## What is E.7 (router slice candidate audit)?

Re-scan of all **187** remaining `@app.*` routes — **Nee extraction**. Result: **3** safe E.8 candidates.

## What is E.8 (DCC alleen-lezen router slice)?

Three GET routes moved to `dev_dashboard_readonly.py`: Terugend-health, Neetifications/status, Neetifications/events. Uses `core.dev_dashboard_Terugend_health` and `core.Neetification_state` only. `app.py`: 17,472→17,425 lines.

## What is F.1 (DCC Status Facade)?

CaNeenical module `core/dcc_status_facade.py` — alleen-lezen aggregation contract for DCC sections. **Nee route migration** in F.1. See `docs/architecture/DCC_STATUS_FACADE_F1_EN.md`.

## What is F.2 (DCC router migration)?

Six aggregation GET routes in `app.py` delegate to `dcc_status_facade`. Nee API changes. See `docs/architecture/DCC_STATUS_ROUTER_MIGRATION_F2_EN.md`.

## What is F.3 (DCC aggregation audit)?

Analysis only (Nee refactoring): remaining direct access, traffic-light duplicates, roadmap subrouter boundary, ai_prompt stub → facade in F.4, Deploy/core coupling. See `docs/architecture/DCC_AGGREGATION_AUDIT_F3_EN.md`.

## What is F.4 (DCC delegation cleanup)?

`ai_prompt_generate_stub` and readonly router endpoints delegate to `dcc_status_facade` API helpers. Nee API changes. See `docs/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`.

## What is G.1 (System Status Facade)?

CaNeenical module `core/system_status_facade.py` — alleen-lezen aggregation for system ampel, Terugend runtime, installation, profile. **Nee route migration** in G.1. Nee Netwerk diagNeestics. See `docs/architecture/SYSTEM_STATUS_FACADE_G1_EN.md`.

## What is G.1b (system status route migration)?

`GET /api/system/status` in `app.py` delegates to `build_system_status()`. Nee API changes. See `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B_EN.md`.

## What is G.2 (Netwerk Info Facade)?

CaNeenical module `core/Netwerk_info_facade.py` — alleen-lezen Netwerk info, demo fallTerug, legacy Neermalization. **Nee route migration** in G.2. Doc: `docs/architecture/Netwerk_INFO_FACADE_G2_EN.md`.

## What is G.2b (Netwerk Route Migration)?

`GET /api/status` (Netwerk block) and `GET /api/system/Netwerk` delegate to `Netwerk_info_facade`. Nee API/response change. Doc: `docs/architecture/Netwerk_INFO_ROUTE_MIGRATION_G2B_EN.md`.

## What is G.3 (Netwerk Core Cleanup)?

`get_system_info` and `webserver_status` delegate to `Netwerk_info_facade`. Legacy `get_Netwerk_info`/`_demo_Netwerk` remain implementation behind facade adapters. Doc: `docs/architecture/Netwerk_INFO_CORE_CLEANUP_G3_EN.md`.

## What is G.4 (Netwerk Handler Extraction)?

`GET /api/status` and `GET /api/system/Netwerk` in `api/routes/Netwerk.py`; facade delegation only. geblokkeerd: `system-info`, `webserver/status`. Doc: `docs/architecture/Netwerk_HANDLER_EXTRACTION_G4_EN.md`.

## What is G.5 (Netwerk Legacy Elimination Audit)?

Full inventory — **Nee refactoring**. 3 legacy functions in `app.py`; 1 facade bypass in `webserver_status`. Volgende candidates: G.6/G.7/G.8. Doc: `docs/architecture/Netwerk_Volgende_FACADE_CANDIDATES_G5_EN.md`.

## What is G.6 (System Info Facade)?

`GET /api/system-info` fully delegates to `system_info_facade`; Netwerk only via `Netwerk_info_facade`; status sections via `dcc_status_facade`. ~240 lines extracted from `app.py`. Doc: `docs/architecture/SYSTEM_INFO_FACADE_G6_EN.md`.

## What is G.7 (Webserver Status Facade)?

`GET /api/webserver/status` delegates to `webserver_status_facade`; Netwerk and port via `Netwerk_info_facade`. G.5 bypass removed. Doc: `docs/architecture/WEBSERVER_STATUS_FACADE_G7_EN.md`.

## What is G.8 (Netwerk Discovery Core)?

Discovery logic moved from `app.py` to `Netwerk_discovery.py`; `Netwerk_info_facade` has Nee lazy `import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/Netwerk_DISCOVERY_CORE_G8_EN.md`.

## What is H.1 (Frontend Status ViewModel)?

CaNeenical module `frontend/src/viewmodels/statusViewModel.ts` — central status Neermalization. **Nee component migration** in H.1. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1_EN.md`.

## What is H.2 (Frontend Status Utility Migration)?

`trafficLightModel`, `DeployDriftTone`, and `toneClass` delegate to `statusViewModel`. Nee UI/color change. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md`.

## What is H.3 (Frontend Status Component Migration)?

3 small DCC components delegate tone mapping to `dashboardLegacyToneFromInput`. Nee UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md`.

## What is H.4 (Frontend Status Component Migration — second slice)?

3 more small components (`ReadyStableSection`, `StatusCard`, `RiskWaarschuwingCard`) delegate to `isDashboardgroenStatus`, `isgroenDashboardTone`/`dashboardToneFromInput`, `riskWaarschuwingTitleKeyForLevel`. Nee UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`.

## What is H.5 (Frontend Status Utility Migration)?

3 small DCC utilities (`governanceMatrix`, `roadmapFilter`, `buildGovernancePrompt`) delegate status mapping to `statusViewModel`. Nee UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5_EN.md`.

## What is H.6 (Frontend Status Presentation Migration)?

5 presentation/utility files delegate to `statusViewModel` (LampDot, panda traffic light, governance history, standalone dashboard). Nee UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H6_EN.md`.

## What is H.7 (Frontend Status — final slice)?

5 presentation libs delegate to `statusViewModel`. Remaining: 10 (domain + large-page). **Nee H.8.** Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7_EN.md`.

## What is G.9 (Hardware Discovery Core)?

Hardware/system discovery extracted from `app.py` to `hardware_discovery.py`; `system_info_facade` has Nee `_legacy_*`/`import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/HARDWARE_DISCOVERY_CORE_G9_EN.md`.

## What is G.11 (Webserver Service Discovery)?

Webserver/service/CMS discovery in `webserver_service_discovery.py`; `webserver_status_facade` without `import app`. Legacy wrappers in `app.py`. Doc: `docs/architecture/WEBSERVER_SERVICE_DISCOVERY_G11_EN.md`.

## What is G.12 (System Status Core)?

Ampel logic (Terugup/Herstel/security/updates) in `system_status_core.py`; facade delegates only. Security/update adapters stay in core. Doc: `docs/architecture/SYSTEM_STATUS_CORE_G12_EN.md`.

## What is P.1 (Storage Discovery CaNeenical)?

CaNeenical lsblk/findmnt/blkid owner `storage_discovery.py`; `storage_facade` delegates. `app.py` storage blocks intentionally deferrood. Matrix: `docs/architecture/STORAGE_DISCOVERY_OWNERSHIP_MATRIX.md`.

## What is D.12 (Deploy Thin-Orchestrator Audit)?

Audit of `Deploy/routes.py` (190 routes, 81 runner imports); final plan without execute extraction. Doc: `docs/architecture/Deploy_THIN_ORCHESTRATOR_FINAL_PLAN.md`.

## Volgende step?

G.13 (remaining `system_status_facade`→app sections) · P.2 (`app.py` storage migration) · D.13 (roodding domain router).

## Further reading

- `docs/architecture/MODULE_CATALOG_EN.md`
- `docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md`
- `docs/architecture/DO_NeeT_DUPLICATE_RULES_EN.md`
- `docs/kNeewledge-base/architecture/CORE_FACADES_EN.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`
- `docs/architecture/Deploy_RUNNER_REGISTRY_EN.md`
- `docs/architecture/Deploy_RUNNER_RESULT_CONTRACT_EN.md`
- `docs/architecture/Deploy_RUNNER_API_FACADE_EN.md`
- `docs/architecture/Deploy_RUNNER_RISK_GATE_EN.md`
- `docs/architecture/Deploy_RUNNER_ROUTES_DECOUPLING_C5_EN.md`
- `docs/architecture/Deploy_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`
