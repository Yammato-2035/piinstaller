# Modul-Katalog (Source of Truth)

**Stand:** nach H.7 (finaler StatusViewModel-Slice, `count_10`) · **Kein Big-Bang** — Inventar und Ownership.

Cursor und Entwickler müssen **vor neuer Implementierung** diesen Katalog, die [Function Ownership Matrix](FUNCTION_OWNERSHIP_MATRIX.md) und [Do-Not-Duplicate Rules](DO_NOT_DUPLICATE_RULES.md) prüfen.

---

## 1. storage_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/storage_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE) |
| **Zweck** | Einheitliche Storage-Discovery: lsblk, blkid, Klassifikation, Inspect-Bundle |
| **Verantwortlichkeiten** | Device Tree, UUID/FS-Typ, Backup/Restore-Kandidaten, Legacy-Normalisierung |
| **Öffentliche API** | `get_block_devices`, `get_mounts`, `classify_storage_target`, `collect_inspect_storage_bundle`, `build_storage_inventory_snapshot`, … |
| **Darf genutzt werden von** | `app.py`, Backup/Restore-Module, Partitionshelfer, Rescue (read-only), Tests |
| **Nicht neu implementieren** | Parallele lsblk/blkid-Parsing-Logik |
| **Legacy-Zugriffe** | `backend/modules/storage_detection.py` (PARTIAL), `safe_device.py`, `device_identity.py` |
| **Migration** | Caller schrittweise auf Facade; Low-Level nur in Allowlist (Boundary-Guard) |
| **Tests** | `test_core_storage_facade_v1`, `test_storage_facade_contracts_v1`, `test_partitions_storage_facade_v1` |
| **Doku DE/EN** | `STORAGE_DISCOVERY_INVENTORY.md`, `CORE_FACADE_RULES.md` |

---

## 2. mount_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/mount_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE) |
| **Zweck** | findmnt, Mount-Inventar, Readonly-Mount-Plan, Source-vs-Target |
| **Öffentliche API** | `build_mount_inventory_snapshot`, `plan_readonly_source_mount`, `build_readonly_mount_plan`, `validate_source_not_target`, `validate_not_live_root` |
| **Darf genutzt werden von** | Rescue readonly mount, Backup target prep, Inspect |
| **Nicht neu implementieren** | findmnt-JSON-Parsing, ad-hoc Mount-Pläne |
| **Legacy** | `modules/inspect_storage.py`, `backup_target_auto_prepare.py` |
| **Tests** | `test_core_mount_facade_v1`, `test_mount_facade_contracts_v1` |
| **Doku** | `CORE_STORAGE_MOUNT_FACADES_2026-05-20.md` |

---

## 3. safety_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/safety_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE) |
| **Zweck** | Write-Target-, Backup-, Restore-, Partition-Validierung; SafetyDecision |
| **Öffentliche API** | `validate_write_target`, `validate_backup_target`, `validate_restore_target`, `validate_partition_target`, `build_safety_decision`, `build_write_safety_summary` |
| **Darf genutzt werden von** | Preflight, Backup/Restore engines, Deploy plan routes (indirekt) |
| **Nicht neu implementieren** | Eigene System-Disk-Checks, parallele Write-Guards |
| **Legacy** | `safe_device.py`, `safety/write_guard.py` (Low-Level, Allowlist) |
| **Tests** | `test_core_safety_facade_v1`, `test_safety_facade_contracts_v1` |
| **Doku** | `CORE_FACADE_RULES.md` |

---

## 4. runner_registry

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/runner_registry.py` |
| **Status** | **CANONICAL_MODULE** (CONTRACT) |
| **Zweck** | Metadaten aller `runner_*.py`: Kategorie, Risk, Capabilities, Policy |
| **Öffentliche API** | `build_runner_registry_from_files`, `find_runner_by_id`, `registry_policy_warnings`, `RunnerRegistryEntry` |
| **Darf genutzt werden von** | `runner_api_facade`, `runner_risk_gate`, `runner_result_contract`, Tests |
| **Nicht neu implementieren** | Ad-hoc Runner-Listen, eigene Risk-Klassifikation in Routen |
| **Tests** | `test_deploy_runner_registry_v1` |
| **Doku** | Deploy D.1–D.9 Architektur-Docs |

---

## 5. runner_result_contract

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/runner_result_contract.py` |
| **Status** | **CANONICAL_MODULE** (CONTRACT) |
| **Zweck** | Einheitliche Runner-Ergebnis-Struktur, Status-Tokens, Evidence-Refs |
| **Öffentliche API** | `RunnerResult`, `RunnerResultStatus`, `validate_runner_result`, `build_empty_result_for_registry_entry` |
| **Darf genutzt werden von** | Facade, Registry, einzelne Runner (Output), Tests |
| **Nicht neu implementieren** | Neue Status-Strings außerhalb Contract |
| **Tests** | `test_deploy_runner_result_contract_v1` |

---

## 6. runner_api_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/runner_api_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE) |
| **Zweck** | Read-only/plan-only API-Zugriff auf Registry, Contract, Risk Gate — **keine** Runner-Ausführung |
| **Öffentliche API** | `build_runner_catalog`, `build_plan_only_response`, `get_runner_risk_gate_decision`, `list_runner_plan_allowed` |
| **Darf genutzt werden von** | Subrouter (`routes_*`), Tests |
| **Nicht neu implementieren** | Direkte `runner_*.py`-Imports in Routern |
| **Tests** | `test_deploy_runner_api_facade_v1`, `test_deploy_runner_routes_decoupling_v1` |

---

## 7. runner_risk_gate

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/runner_risk_gate.py` |
| **Status** | **CANONICAL_MODULE** (CONTRACT) |
| **Zweck** | C.4 Entscheidungen: `allowed_to_plan`, `allowed_to_execute`, Operator-Pflicht |
| **Öffentliche API** | `evaluate_runner_risk_gate`, `RunnerRiskDecision`, `build_risk_gate_summary` |
| **Darf genutzt werden von** | `runner_api_facade`, Tests, Doku |
| **Nicht neu implementieren** | Parallele Execute-Freigabe in Routen |
| **Tests** | `test_deploy_runner_risk_gate_v1` |

---

## 8. routes_registry

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_registry.py` |
| **Status** | **ROUTER** (D.2) |
| **Zweck** | 5 GET Facade-Routen: Catalog, Summary, Policy, Entry, Empty-Result |
| **Routen** | `/runners/catalog`, `/runners/summary`, … |
| **Darf genutzt werden von** | `routes.py` via `include_router` |
| **Tests** | `test_deploy_routes_registry_v1` |

---

## 9. routes_risk_gate

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_risk_gate.py` |
| **Status** | **ROUTER** (D.3) |
| **Zweck** | 5 GET Risk-Gate-Routen |
| **Tests** | `test_deploy_routes_risk_gate_v1` |

---

## 10. routes_evidence

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_evidence.py` |
| **Status** | **ROUTER** (D.4/D.7) |
| **Zweck** | 12 POST plan-only Evidence-Routen via `build_plan_only_response` |
| **Tests** | `test_deploy_routes_evidence_v1` |

---

## 11. routes_governance

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_governance.py` |
| **Status** | **ROUTER** (D.5) |
| **Zweck** | 3 POST Governance plan-only (C.5) |
| **Tests** | `test_deploy_routes_governance_v1` |

---

## 12. routes_diagnostics

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_diagnostics.py` |
| **Status** | **ROUTER** (D.8) |
| **Zweck** | 6 POST Diagnostics plan-only |
| **Tests** | `test_deploy_routes_diagnostics_v1` |

---

## 13. routes_versioning

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_versioning.py` |
| **Status** | **ROUTER** (D.10) |
| **Zweck** | 8 POST Versioning/Identifier plan-only |
| **Öffentliche API** | `build_plan_only_response` via `runner_api_facade` |
| **Tests** | `test_deploy_routes_versioning_v1` |
| **Doku** | `DEPLOY_VERSIONING_ROUTER_EXTRACTION_D10.md` |

---

## 14. routes_runtime

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes_runtime.py` |
| **Status** | **ROUTER** (D.11) |
| **Zweck** | 8 POST Runtime-Status/Readiness plan-only |
| **Tests** | `test_deploy_routes_runtime_v1` |
| **Doku** | `DEPLOY_RUNTIME_ROUTER_EXTRACTION_D11.md` |

---

## 15. dcc_status_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/dcc_status_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE, F.1) |
| **Zweck** | Einheitliche read-only DCC-Statusaggregation; Section-Contracts; Legacy-Normalisierung |
| **Öffentliche API** | `build_dcc_status_overview`, `build_dcc_roadmap_overview`, `build_dcc_backend_health_section`, `build_dcc_notification_section`, `build_dcc_evidence_section`, `build_dcc_facade_diagnostics`, `build_section_status`, `normalize_legacy_*` |
| **Delegiert an** | `dev_dashboard`, `dev_dashboard_roadmap`, `dev_dashboard_backend_health`, `notification_state` |
| **Darf genutzt werden von** | `app.py` (F.2 migriert), `dev_dashboard_status_service`, DCC-Router, Tests |
| **Nicht neu implementieren** | Parallele `build_dashboard_status`-Aufrufe in Routern; neue Ampel-Mapping-Logik außerhalb Facade |
| **Profil-Gate** | bleibt `core.dev_dashboard_status_service` (nicht duplizieren) |
| **Tests** | `test_dcc_status_facade_v1`, `test_dcc_status_facade_router_migration_v1` |
| **Doku DE/EN** | `DCC_STATUS_FACADE_F1.md`, `DCC_AGGREGATION_AUDIT_F3.md` |
| **F.3 Audit** | Verbleibend: `deploy_job_state`; Subrouter `boundary_ok` |
| **F.4 Delegation** | ai_prompt + readonly E.8/evidence → Facade-API-Helper |

---

## 16. system_status_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/system_status_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE, G.1) |
| **Zweck** | Systemstatus-Aggregation für `/api/status` und `/api/system/status` (Vorbereitung) |
| **Öffentliche API** | `build_system_status`, `build_system_status_sections`, `build_backend_runtime_section`, `build_installation_section`, `build_profile_section`, `build_system_status_diagnostics`, `normalize_legacy_system_status` |
| **Delegiert an** | `app._compute_system_status`, `app.APP_SETTINGS`, `install_paths`, app version/profile helpers |
| **Ausgeschlossen G.1** | Netzwerk (`get_network_info`) → G.2 |
| **Tests** | `test_system_status_facade_v1` |
| **Doku DE/EN** | `SYSTEM_STATUS_FACADE_G1.md` |

---

## 17a. network_discovery

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/network_discovery.py` |
| **Status** | **CANONICAL_MODULE** (G.8) |
| **Zweck** | Read-only Network-Discovery (ip/hostname/ss) |
| **Öffentliche API** | `discover_network_info`, `discover_demo_network`, `detect_frontend_port`, `build_network_discovery_diagnostics` |
| **Legacy-Wrapper** | `app.get_network_info`, `app._demo_network`, `app._detect_frontend_port` |
| **Tests** | `test_network_discovery_v1`, `test_network_facade_without_app_dependency_g8` |
| **Doku DE/EN** | `NETWORK_DISCOVERY_CORE_G8.md` |

---

## 17. network_info_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/network_info_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE, G.2) |
| **Zweck** | Netzwerk-Info read-only; Demo-Fallback; Normalisierung |
| **Öffentliche API** | `build_network_info`, `detect_frontend_port`, `build_demo_network_info`, `build_system_network_response`, … |
| **HTTP migriert** | `GET /api/status`, `/api/system/network` (G.4 Router); Network-Block: `/api/system-info` (G.3) |
| **Delegiert an** | `network_discovery` (G.8); `app._is_demo_mode` (HTTP) |
| **Discovery-Owner** | `core/network_discovery.py` — kanonisch seit G.8 |
| **Ausgeschlossen** | Netzwerk-Schreiboperationen, nmcli write |
| **Tests** | `test_network_info_facade_v1` |
| **Doku DE/EN** | `NETWORK_INFO_FACADE_G2.md` |

---

## 17b. webserver_status_facade

| Feld | Wert |
|------|------|
| **Pfad** | `backend/core/webserver_status_facade.py` |
| **Status** | **CANONICAL_MODULE** (FACADE, G.7) |
| **Zweck** | Webserver/CMS/Service-Status read-only für `GET /api/webserver/status` |
| **Öffentliche API** | `build_webserver_status`, `build_webserver_status_section`, `build_webserver_frontend_section`, `build_webserver_status_diagnostics` |
| **HTTP migriert** | `GET /api/webserver/status` (G.7) |
| **Delegiert an** | `network_info_facade` (Network+Port); `app.get_running_services`, `app.run_command`, … |
| **Tests** | `test_webserver_status_facade_v1`, `test_webserver_status_route_migration_g7` |
| **Doku DE/EN** | `WEBSERVER_STATUS_FACADE_G7.md` |

---

## 18. frontend_status_viewmodel

| Feld | Wert |
|------|------|
| **Pfad** | `frontend/src/viewmodels/statusViewModel.ts` |
| **Status** | **CANONICAL_MODULE** (VIEWMODEL, H.1) |
| **Zweck** | Frontend Status-Normalisierung, Ampel/Severity/Blocking |
| **Öffentliche API** | `normalizeStatusKind`, `buildStatusViewModel`, `buildTrafficLightViewModel`, `buildDashboardStatusViewModel` |
| **Komponenten/Utils (H.3–H.7)** | 6 Komponenten · 8 Libs · H.7 final: riskLevels, devDashboardFilters, trafficLightModel, RoadmapDrawer, setuphelferToolTheme |
| **Tests** | `statusViewModel.test.ts` (Vitest) |
| **Doku DE/EN** | `FRONTEND_STATUS_VIEWMODEL_H1.md` |

---

## Referenz: routes.py (Legacy-Orchestrator)

| Feld | Wert |
|------|------|
| **Pfad** | `backend/deploy/routes.py` |
| **Status** | **LEGACY** (Orchestrator + Monolith) |
| **Zweck** | `include_router` für 7 Subrouter; verbleibende Execute/Rescue/Write-Routen |
| **Metriken** | ~4120 Zeilen, 81 direkte Runner-Imports |
| **Migration** | E.1+ sequenziell; Ziel <500 Zeilen (`DEPLOY_ROUTES_THIN_ORCHESTRATOR_TARGET_D6.md`) |

---

## Kandidaten / geplant

| Modul | Status | Nächster Schritt |
|-------|--------|------------------|
| `api/routes/health.py` | **CANONICAL_ROUTER** (E.1) | `/health`, `/api/init/status`, `/api/logs/path` |
| `api/routes/version.py` | **CANONICAL_ROUTER** (E.1) | `/api/version` |
| `api/routes/settings.py` | **CANONICAL_ROUTER** (E.2) | `GET /api/settings`, notifications/email |
| `api/routes/status.py` | **CANONICAL_ROUTER** (E.2/E.3) | presets, debug, user-profile, self-update/status |
| `api/routes/capabilities.py` | **CANONICAL_ROUTER** (E.3) | DCC capability/compact-status |
| `api/routes/catalog.py` | **CANONICAL_ROUTER** (E.3) | `/api/apps` |
| `api/routes/dev_dashboard_readonly.py` | **CANONICAL_ROUTER** (E.4/E.8) | DCC modules/evidence + backend-health + notifications read |
| `api/routes/dev_dashboard_roadmap.py` | **CANONICAL_ROUTER** (E.5/E.6) | roadmap registry + next-prompts/export |
| `api/routes/network.py` | **CANONICAL_ROUTER** (G.4) | `GET /api/status`, `GET /api/system/network` |
| `app.py` Router-Slices | **IN_PROGRESS** | G.6 / G.7 / G.8 (siehe G.5 Audit) |
| `frontend_status_viewmodel` | **CANONICAL_MODULE** (H.1–H.7 final) | count_10 verbleibend (Domain/Large-Page) |
| `dcc_status_facade` | **CANONICAL_MODULE** (F.1–F.4) | HTTP-DCC-Leser delegiert |
| `system_status_facade` | **CANONICAL_MODULE** (G.1/G.1b) | `/api/system/status` migriert |
| `network_info_facade` | **CANONICAL_MODULE** (G.2–G.5) | Facade + Router; Legacy in `app.py` |
| **webserver_status_facade** | **CANONICAL_MODULE** (G.7) | `GET /api/webserver/status` — erledigt |
| **network_discovery** | **CANONICAL_MODULE** (G.8) | Discovery-Owner — erledigt |
| **system_info_facade** | **CANDIDATE** (G.6) | `GET /api/system-info` — HIGH |
| **frontend_runtime_facade** | **CANDIDATE** (G.5) | Port-Erkennung — MEDIUM |
| **Dev Dashboard Aggregation Facade** | **CANDIDATE** (E.7) | control-center-summary, prompt-findings (nutzt Facade F.2+) |
| `routes_notifications.py` | **blocked** | D.9 no_safe_slice |

---

## Pflege

Neues Modul: zuerst hier als **CANDIDATE** eintragen, dann implementieren. Siehe [CURSOR_PROMPT_MODULE_REUSE_HEADER.md](../developer/CURSOR_PROMPT_MODULE_REUSE_HEADER.md).
