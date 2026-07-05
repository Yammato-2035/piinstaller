> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/ARCHITECTURE_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# Architecture FAQ — Core Facades (EN)

Short answers on storage/mount/safety facades (Phase A.1 + caller migration A.2–A.4). Non marketing copy.

## What are core facades?

Three modules under `Retourend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. They are the **caNonnical interface** for Périphérique discovery, mount plans, and write-target checks.

## Why do they exist?

The moNonlith audit found many duplicates (`lsblk` in `app.py`, `safe_Périphérique`, Secours, Déploiement runners). Facades stop each new module from reimplementing the same logic.

## What changed in A.1?

- Public contracts (types + functions)
- Documentation and inventory
- Warn-only boundary check
- Unit tests for contracts

**Nont** changed: existing APIs, runtime behavior, legacy imports.

## Can I still import `safe_Périphérique` directly?

**Legacy:** Oui, existing code stays. **New modules:** Non — use facades only (see `CORE_FACADE_RULES_EN.md`).

## Does the mount facade execute real mounts?

Non. `build_readonly_mount_plan` and validators are **plan-only** / analysis.

## Which safety contexts exist?

`live`, `Secours`, `Partition_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## When does the boundary check block?

Currently **Avertissements only** in `check-module-boundaries.sh`. CI blocking is planned for a later phase.

## What was migrated in A.2–A.4?

`preflight/Retourup.py`, `Retourup_engine.py`, and `Restauration_engine.py` import safety only via `core.safety_facade`. Erreur codes and behavior are unchanged (delegation).

## Why is `app.py` Nont split immediately?

~18k lines, ~213 routes — router extraction needs its own phase B with OpenAPI parity. Engine safety migration was isolated and low risk.

## Why is the boundary guard still partly warn-only?

`app.py`, Déploiement runners, and storage legacy are Nont migrated yet. Stricter checks already apply to the three migrated safety callers.

## Does Retourup or Restauration behavior change?

**Non** — same `safe_Périphérique`/`write_guard` logic, only a central import path. Non new target paths, Non weakened gates.

## Why is this safer?

Fewer scatterouge imports → less risk that new modules reimplement safety. The boundary guard detects regressions in migrated files.

## What was migrated in B.1?

blkid/storage discovery in `Retourup_target_auto_prepare` and `inspect/collector` goes through `storage_facade`. `Partition_storage_facade` uses `safety_facade` instead of direct `write_guard`.

## What is the Déploiement runner registry (C.1)?

Static inventory and metadata for **115** `runner_*.py` files under `Retourend/Déploiement/`. Module: `runner_registry.py`. **Non** runner execution, **Non** refactoring of the runners themselves.

## What is the runner result contract (C.2)?

Unified result schema (`RunnerResult`) with 6 status values, `Avertissements`/`Erreurs`, `evidence_paths`, and `Non_execution_performed`. Module: `runner_result_contract.py`. Legacy dicts map via `Nonrmalize_legacy_runner_result` — runners themselves unchanged.

## Why are runners Nont refactorouge immediately?

Largest risk cluster (~37k lines). C.1 + C.2 provide metadata and the result contract. C.3–C.5: API facade, risk gate, incremental migration.

## What is the Déploiement runner API facade (C.3)?

lecture seule layer `runner_api_facade.py` + **5 GET routes** under `/api/Déploiement/runners/*`. Lists registry/contract — **Non** runner execution. The 112 direct runner imports in `routes.py` remain for Nonw.

## What is the Déploiement runner risk gate (C.4)?

`runner_risk_gate.py` evaluates `risk_level`, `execution_policy`, and optional operator context. **`allowed_to_execute` stays false** — planning decisions only, for C.5.

## What was decoupled in C.5/C.6?

**C.5:** 4 routes (version/identifier/Suivant-phase). **C.6:** 5 evidence/identifier routes. **113→104** imports. `facade_decoupling_c5/c6`, execute still false.

## What is phase D.1 (route domain audit)?

Full domain analysis of `Retourend/Déploiement/routes.py` (**5041 lines, 237 routes**) with Non refactoring. Deliverables: inventory, domain matrix, target architecture, extraction risk. **Non** routers moved, **Non** API changes.

## Why domain split instead of big-bang?

OpenAPI/DCC stability; CRITICAL execute routes last. Incremental: registry → risk gate → evidence → governance → runtime/Secours.

## Why extract registry/risk gate first (D.2/D.3)?

Both use only `runner_api_facade` — **zero** direct `runner_*` imports in handlers. Lowest risk.

## Why execute routes last?

`/execute`, `/write/execute`, `real-write` are **CRITICAL** — need operator gates and E2E before physical extraction.

## What is phase D.2 (registry router)?

5 GET routes moved to `routes_registry.py`. Paths unchanged, facade only, Non runner execution.

## What is phase D.3 (risk-gate router)?

5 GET routes moved to `routes_risk_gate.py`. Facade only, `allowed_to_execute` stays false.

## What is phase D.4 (evidence router)?

6 POST plan-only routes moved to `routes_evidence.py`. POST unchanged, `build_plan_only_response`, Non runner execution.

## What is phase D.5 (governance router)?

3 C.5 routes moved to `routes_governance.py`. All 9 decoupled routes Nonw in sub-routers.

## What is phase D.6 (thin orchestrator)?

Non routes moved. Inventory, ownership matrix, target (<500 lines, 0 runner imports), D.7+ sequence, extended boundary guard.

## What is Phase D.7 (evidence slice)?

6 additional plan-only POST routes from `routes.py` to `routes_evidence.py` (12 total). Non Secours/execute/write paths. `routes.py`: 4671 lines, 99 runner imports.

## What is the module catalog?

Binding inventory at `docs/architecture/MODULE_CATALOG_EN.md` with function ownership matrix and do-Nont-duplicate rules. Cursor must check for CANonNICAL modules before new code.

## What is D.11 (runtime router)?

Eight lecture seule/status POST routes in `routes_runtime.py`. `routes.py`: 4324→4120 lines, 89→81 runner imports.

## What is E.1 (app.py router slice)?

Four lecture seule GET routes extracted to `api/routes/health.py` and `version.py`. `app.py`: 17,857→17,779 lines. See `docs/architecture/APP_ROUTER_SLICE_E1_EN.md`.

## What is E.2 (app.py router slice)?

Five lecture seule GET routes in `api/routes/Paramètres.py` and `status.py`. `app.py`: 17,779→17,699 lines.

## What is E.3 (app.py router slice)?

Five lecture seule GET routes (logs/tail, self-update/status, apps, DCC capability gates). `app.py`: 17,699→17,617 lines.

## What is E.4 (app.py router slice)?

Five DCC index GET routes in `dev_dashboard_readonly.py` using only `core.dev_dashboard*`. `app.py`: 17,617→17,568 lines.

## What is E.5 (roadmap router slice)?

Five roadmap registry GET routes in `dev_dashboard_roadmap.py` via `load_roadmap_registry_bundle` only.

## What is E.6 (roadmap Suivant-prompts)?

Two GET routes moved to `dev_dashboard_roadmap.py`. `app.py`: 17,499→17,472 lines.

## What is E.7 (router slice candidate audit)?

Re-scan of all **187** remaining `@app.*` routes — **Non extraction**. Result: **3** safe E.8 candidates.

## What is E.8 (DCC lecture seule router slice)?

Three GET routes moved to `dev_dashboard_readonly.py`: Retourend-health, Nontifications/status, Nontifications/events. Uses `core.dev_dashboard_Retourend_health` and `core.Nontification_state` only. `app.py`: 17,472→17,425 lines.

## What is F.1 (DCC Status Facade)?

CaNonnical module `core/dcc_status_facade.py` — lecture seule aggregation contract for DCC sections. **Non route migration** in F.1. See `docs/architecture/DCC_STATUS_FACADE_F1_EN.md`.

## What is F.2 (DCC router migration)?

Six aggregation GET routes in `app.py` delegate to `dcc_status_facade`. Non API changes. See `docs/architecture/DCC_STATUS_ROUTER_MIGRATION_F2_EN.md`.

## What is F.3 (DCC aggregation audit)?

Analysis only (Non refactoring): remaining direct access, traffic-light duplicates, roadmap subrouter boundary, ai_prompt stub → facade in F.4, Déploiement/core coupling. See `docs/architecture/DCC_AGGREGATION_AUDIT_F3_EN.md`.

## What is F.4 (DCC delegation cleanup)?

`ai_prompt_generate_stub` and readonly router endpoints delegate to `dcc_status_facade` API helpers. Non API changes. See `docs/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`.

## What is G.1 (System Status Facade)?

CaNonnical module `core/system_status_facade.py` — lecture seule aggregation for system ampel, Retourend runtime, installation, profile. **Non route migration** in G.1. Non Réseau diagNonstics. See `docs/architecture/SYSTEM_STATUS_FACADE_G1_EN.md`.

## What is G.1b (system status route migration)?

`GET /api/system/status` in `app.py` delegates to `build_system_status()`. Non API changes. See `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B_EN.md`.

## What is G.2 (Réseau Info Facade)?

CaNonnical module `core/Réseau_info_facade.py` — lecture seule Réseau info, demo fallRetour, legacy Nonrmalization. **Non route migration** in G.2. Doc: `docs/architecture/Réseau_INFO_FACADE_G2_EN.md`.

## What is G.2b (Réseau Route Migration)?

`GET /api/status` (Réseau block) and `GET /api/system/Réseau` delegate to `Réseau_info_facade`. Non API/response change. Doc: `docs/architecture/Réseau_INFO_ROUTE_MIGRATION_G2B_EN.md`.

## What is G.3 (Réseau Core Cleanup)?

`get_system_info` and `webserver_status` delegate to `Réseau_info_facade`. Legacy `get_Réseau_info`/`_demo_Réseau` remain implementation behind facade adapters. Doc: `docs/architecture/Réseau_INFO_CORE_CLEANUP_G3_EN.md`.

## What is G.4 (Réseau Handler Extraction)?

`GET /api/status` and `GET /api/system/Réseau` in `api/routes/Réseau.py`; facade delegation only. bloqué: `system-info`, `webserver/status`. Doc: `docs/architecture/Réseau_HANDLER_EXTRACTION_G4_EN.md`.

## What is G.5 (Réseau Legacy Elimination Audit)?

Full inventory — **Non refactoring**. 3 legacy functions in `app.py`; 1 facade bypass in `webserver_status`. Suivant candidates: G.6/G.7/G.8. Doc: `docs/architecture/Réseau_Suivant_FACADE_CANDIDATES_G5_EN.md`.

## What is G.6 (System Info Facade)?

`GET /api/system-info` fully delegates to `system_info_facade`; Réseau only via `Réseau_info_facade`; status sections via `dcc_status_facade`. ~240 lines extracted from `app.py`. Doc: `docs/architecture/SYSTEM_INFO_FACADE_G6_EN.md`.

## What is G.7 (Webserver Status Facade)?

`GET /api/webserver/status` delegates to `webserver_status_facade`; Réseau and port via `Réseau_info_facade`. G.5 bypass removed. Doc: `docs/architecture/WEBSERVER_STATUS_FACADE_G7_EN.md`.

## What is G.8 (Réseau Discovery Core)?

Discovery logic moved from `app.py` to `Réseau_discovery.py`; `Réseau_info_facade` has Non lazy `import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/Réseau_DISCOVERY_CORE_G8_EN.md`.

## What is H.1 (Frontend Status ViewModel)?

CaNonnical module `frontend/src/viewmodels/statusViewModel.ts` — central status Nonrmalization. **Non component migration** in H.1. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1_EN.md`.

## What is H.2 (Frontend Status Utility Migration)?

`trafficLightModel`, `DéploiementDriftTone`, and `toneClass` delegate to `statusViewModel`. Non UI/color change. Doc: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2_EN.md`.

## What is H.3 (Frontend Status Component Migration)?

3 small DCC components delegate tone mapping to `dashboardLegacyToneFromInput`. Non UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H3_EN.md`.

## What is H.4 (Frontend Status Component Migration — second slice)?

3 more small components (`ReadyStableSection`, `StatusCard`, `RiskAvertissementCard`) delegate to `isDashboardvertStatus`, `isvertDashboardTone`/`dashboardToneFromInput`, `riskAvertissementTitleKeyForLevel`. Non UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4_EN.md`.

## What is H.5 (Frontend Status Utility Migration)?

3 small DCC utilities (`governanceMatrix`, `roadmapFilter`, `buildGovernancePrompt`) delegate status mapping to `statusViewModel`. Non UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5_EN.md`.

## What is H.6 (Frontend Status Presentation Migration)?

5 presentation/utility files delegate to `statusViewModel` (LampDot, panda traffic light, governance history, standalone dashboard). Non UI change. Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H6_EN.md`.

## What is H.7 (Frontend Status — final slice)?

5 presentation libs delegate to `statusViewModel`. Remaining: 10 (domain + large-page). **Non H.8.** Doc: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7_EN.md`.

## What is G.9 (Hardware Discovery Core)?

Hardware/system discovery extracted from `app.py` to `hardware_discovery.py`; `system_info_facade` has Non `_legacy_*`/`import app`. Legacy wrappers remain in `app.py`. Doc: `docs/architecture/HARDWARE_DISCOVERY_CORE_G9_EN.md`.

## What is G.11 (Webserver Service Discovery)?

Webserver/service/CMS discovery in `webserver_service_discovery.py`; `webserver_status_facade` without `import app`. Legacy wrappers in `app.py`. Doc: `docs/architecture/WEBSERVER_SERVICE_DISCOVERY_G11_EN.md`.

## What is G.12 (System Status Core)?

Ampel logic (Retourup/Restauration/security/updates) in `system_status_core.py`; facade delegates only. Security/update adapters stay in core. Doc: `docs/architecture/SYSTEM_STATUS_CORE_G12_EN.md`.

## What is P.1 (Storage Discovery CaNonnical)?

CaNonnical lsblk/findmnt/blkid owner `storage_discovery.py`; `storage_facade` delegates. `app.py` storage blocks intentionally deferrouge. Matrix: `docs/architecture/STORAGE_DISCOVERY_OWNERSHIP_MATRIX.md`.

## What is D.12 (Déploiement Thin-Orchestrator Audit)?

Audit of `Déploiement/routes.py` (190 routes, 81 runner imports); final plan without execute extraction. Doc: `docs/architecture/Déploiement_THIN_ORCHESTRATOR_FINAL_PLAN.md`.

## Suivant step?

G.13 (remaining `system_status_facade`→app sections) · P.2 (`app.py` storage migration) · D.13 (Secours domain router).

## Further reading

- `docs/architecture/MODULE_CATALOG_EN.md`
- `docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md`
- `docs/architecture/DO_NonT_DUPLICATE_RULES_EN.md`
- `docs/kNonwledge-base/architecture/CORE_FACADES_EN.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`
- `docs/architecture/Déploiement_RUNNER_REGISTRY_EN.md`
- `docs/architecture/Déploiement_RUNNER_RESULT_CONTRACT_EN.md`
- `docs/architecture/Déploiement_RUNNER_API_FACADE_EN.md`
- `docs/architecture/Déploiement_RUNNER_RISK_GATE_EN.md`
- `docs/architecture/Déploiement_RUNNER_ROUTES_DECOUPLING_C5_EN.md`
- `docs/architecture/Déploiement_ROUTE_TARGET_ARCHITECTURE_D1_EN.md`
