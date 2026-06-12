# Modul-Katalog (Source of Truth)

**Stand:** nach D.9 (`0427de6`) · **Kein Refactoring** — nur Inventar und Ownership.

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
| `app.py` Router-Slices | **CANDIDATE** | E.1 |
| `routes_notifications.py` | **blocked** | D.9 no_safe_slice |

---

## Pflege

Neues Modul: zuerst hier als **CANDIDATE** eintragen, dann implementieren. Siehe [CURSOR_PROMPT_MODULE_REUSE_HEADER.md](../developer/CURSOR_PROMPT_MODULE_REUSE_HEADER.md).
