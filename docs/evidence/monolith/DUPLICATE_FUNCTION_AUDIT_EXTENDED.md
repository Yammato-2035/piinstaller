# Duplicate Function Audit (Extended)

**Datum:** 2026-06-10  
**HEAD:** `9005c54` · **Update F.2:** `app.py` DCC-Aggregation über Facade — ein Mapping-Pfad für HTTP.

## Zusammenfassung

| Kategorie | Duplikat-Cluster | Schwere | Empfehlung |
|-----------|------------------|---------|------------|
| SHA256 / Hashing | 3+ Muster | MEDIUM | Zentrale `core/hash_utils.py` |
| Storage Discovery | 4 Module | HIGH | `storage_facade` konsolidieren |
| Mount / Safe Device | 3 Module | HIGH | `mount_facade` als Single Entry |
| Backup Target Validation | 4 Module | HIGH | `backup_target_service_access` vereinheitlichen |
| Device Classification | 5+ Klassifikatoren | HIGH | Rollen-Matrix dokumentieren, Facade |
| Manifest Handling | 3 Manifest-Systeme | HIGH | Deploy vs Profile vs Rescue trennen |
| Deploy Drift | 4+ Implementierungen | MEDIUM | Ein Drift-Contract |
| Dashboard Status | 6+ Aggregatoren | HIGH | DCC Status Service als Facade |
| Notifications | 4 Module | MEDIUM | `notification_service` als Orchestrator |
| Telemetrie | 4 Module | MEDIUM | Rescue-Telemetrie-Pipeline |
| Runtime Gates | 3 Skripte + Core | LOW | Bereits teilweise konsolidiert |
| API Wrapper (Frontend) | 5+ Clients | MEDIUM | Domain-APIs über `fetchApi` |
| i18n | 2 große JSON + Rescue-i18n | MEDIUM | Domain-Namespaces |
| Hardstop / Write Guard | 4 Module | HIGH | `safety_facade` erweitern |
| Verify | 3+ Pfade | MEDIUM | Verify-Contract |

---

## 1. Storage Discovery

| Implementierung | Pfad | Domäne |
|-----------------|------|--------|
| `storage_detection` | `backend/modules/storage_detection.py` | Backup Target Validation |
| `safe_device` | `backend/core/safe_device.py` | Write Guard |
| `storage_facade` | `backend/core/storage_facade.py` | Facade (teilweise) |
| `partition_storage_facade` | `backend/core/partition_storage_facade.py` | Partitionshelfer |
| `runner_rescue_storage_discovery` | `backend/deploy/runner_rescue_storage_discovery.py` | Rescue Deploy |

**Überschneidung:** lsblk/blkid-Parsing, removable/USB-Erkennung, Backup-Ziel-Prüfung.  
**Risiko:** Inkonsistente Klassifikation zwischen Backup und Partitionshelfer (historisch behoben für USB-HDD, Pattern bleibt).

---

## 2. Mounting / Safe Device

| Modul | Pfad |
|-------|------|
| `mount_facade` | `backend/core/mount_facade.py` |
| `safe_device` | `backend/core/safe_device.py` |
| `rescue_fat32_esp_usb_writer` | `backend/core/rescue_fat32_esp_usb_writer.py` (eigene Mount-Logik) |

**Überschneidung:** Mount-Pfade, Read-only-Erzwingung, Geräte-Exklusion.

---

## 3. Device Classification

| Klassifikator | Domäne |
|---------------|--------|
| `storage_role_classification.py` | Partitionshelfer |
| `inspect/classifier.py` | Diagnostics / Inspect |
| `rescue_iso_uefi_classify.py` | Rescue ISO |
| `runner_legacy_identifier_cleanup_classifier.py` | Deploy / Migration |
| `rescue_target_assessment.py` | Rescue Restore |
| `backup_tar_warning_classification.py` | Backup |

**Überschneidung:** „Ist das ein Systemlaufwerk?“ — mehrere Heuristiken parallel.

---

## 4. SHA256 / Verify

| Muster | Vorkommen |
|--------|-----------|
| `hashlib.sha256` inline | 80+ Dateien (Deploy-Runner, Tests, Core) |
| `sha256_file()` Hilfsfunktion | `rescue_fat32_esp_*`, `modules/backup_verify.py` |
| `compute_payload_hash` | `rescue_telemetry_ingest.py` |
| Manifest-Snapshot-Hash | `runner_manual_runtime_*` |

**Überschneidung:** Kanonisierung, Datei-Hash, Payload-Hash — keine einheitliche Bibliothek.

---

## 5. Manifest Handling

| System | Pfad | Zweck |
|--------|------|-------|
| `deploy_manifest.py` | `backend/core/` | Workspace ↔ Runtime Deploy |
| `profile_deploy_manifest.py` | `backend/core/` | Profil-Gate Drift |
| `generate_deploy_manifest.py` | `backend/tools/` | Manifest-Erzeugung |
| Rescue MANIFEST.json | `build/rescue/` | Stick/ISO Payload |

**Überschneidung:** SHA256-Felder, Pfad-Listen, Drift-Vergleich — unterschiedliche Schemas.

---

## 6. Deploy Drift / Runtime Gates

| Implementierung | Ort |
|-----------------|-----|
| `profile_deploy_drift` Tests + Core | `backend/core/profile_deploy_manifest.py` |
| `runtime_deploy_gate_eval.py` | `scripts/` |
| `deploy_runtime_verify.py` | `backend/core/` |
| `governanceMatrix.ts` | `frontend/src/lib/devDashboard/` |
| `dccCompactStatus.ts` | Frontend DCC |

**Überschneidung:** Workspace/Runtime-Vergleich in Backend und Frontend parallel modelliert.

---

## 7. Dashboard Status Mapping

| Modul | Zeilen |
|-------|--------|
| `dev_dashboard.py` | 1.217 |
| `dev_dashboard_compact_status.py` | ~400 |
| `dev_dashboard_status_service.py` | ~350 |
| `dev_dashboard_cockpit.py` | 731 |
| `dev_control_center_summary.py` | 477 |
| `dev_dashboard_backend_health.py` | ~300 |
| `buildStandaloneDashboard.ts` | Frontend |
| `loadDevDashboard.ts` | Frontend |

**Überschneidung:** Status-Aggregation, Ampellogik, Modul-Checks — mehrfach transformiert.

---

## 8. Notification System

| Modul | Rolle |
|-------|-------|
| `notification_service.py` | Orchestrator |
| `notification_settings.py` | Konfiguration |
| `notification_state.py` | Persistenz |
| `notification_events.py` | Event-Typen |
| `notification_email.py` | Transport |

**Bewertung:** Teilweise beabsichtigte Trennung, aber API-Oberfläche über `app.py` verstreut.

---

## 9. Telemetrie

| Modul | Domäne |
|-------|--------|
| `rescue_telemetry_ingest.py` | Rescue Agent Ingest |
| `rescue_telemetry_lan_proxy.py` | LAN Proxy |
| `rescue_telemetry_tasks.py` | Background Tasks |
| `rescue_network_telemetry_gate.py` | Gate |
| `backup_telemetry.py` | Backup |

---

## 10. Frontend API Wrapper

| Client | Pfad |
|--------|------|
| `api.ts` | Zentraler `fetchApi`, API-Base |
| `partitionApi.ts` | Partitionshelfer |
| `devServerApi.ts` | Development Server |
| `diagnosticsApi.ts` | Diagnostics |
| Inline `fetchApi` in Pages | BackupRestore, Dashboard, Settings, … |

**Überschneidung:** Fehlerbehandlung, Timeout, Demo-Mode — teils dupliziert in Pages.

---

## 11. i18n

| Quelle | Umfang |
|--------|--------|
| `frontend/src/locales/de.json` | 3.379 Zeilen — alle Domänen |
| `frontend/src/locales/en.json` | 3.379 Zeilen |
| `frontend/src/rescue/i18n/` | Rescue-spezifisch |
| `backend/core/backup_recovery_i18n.py` | Backend-Strings |

**Überschneidung:** Backup/Restore-Texte in FAQ, Frontend-i18n und Backend-i18n.

---

## 12. Hardstop / Write Guard

| Modul | Domäne |
|-------|--------|
| `partition_hardstop.py` / API routes | Partitionshelfer |
| `rescue_hardstop.py` | Rescue |
| `safety_facade.py` | Querschnitt |
| `real_write_guard.py` | Deploy Write |
| `safe_device.py` | Storage |

---

## Duplikat-Risiko-Matrix

| Risiko | Cluster |
|--------|---------|
| **CRITICAL** | Device Classification (Safety), Write Guard |
| **HIGH** | Storage Discovery, Dashboard Status, Manifest Drift |
| **MEDIUM** | SHA256, Telemetrie, i18n, API Wrapper |
| **LOW** | Runtime Gates (bereits teilweise vereinheitlicht) |

**Geschätzte Duplikat-Cluster:** 14 Hauptbereiche, ~35 konkrete Modul-Paare

---

## Update: Facade Caller Migration A.2–A.4 (2026-06-10)

| Cluster | Status |
|---------|--------|
| Write Guard / `preflight/backup.py` | **migriert** → `safety_facade.evaluate_preflight_write_target` |
| Safe Device / `backup_engine.py` | **migriert** → `safety_facade.validate_write_target` |
| Safe Device / `restore_engine.py` | **migriert** → `safety_facade.validate_write_target` |
| Write Guard / `app.py` | offen (Phase B Router) |
| Write Guard / `partition_storage_facade.py` | offen (Phase B.1 Storage) |

Boundary: 3 Safety-Warnungen entfernt. Evidence: `BOUNDARY_WARNINGS_FINAL_PHASE_A2_A4.txt`

---

## Update: Storage Facade Migration B.1 (2026-06-10)

| Cluster | Status |
|---------|--------|
| blkid / `backup_target_auto_prepare.py` | **migriert** → `storage_facade.get_partition_uuid` |
| `storage_detection` / `inspect/collector.py` | **migriert** → `collect_inspect_storage_bundle` |
| write_guard / `partition_storage_facade.py` | **migriert** → `safety_facade` |
| lsblk/findmnt / `app.py` | offen (B.2) |

Evidence: `BOUNDARY_WARNINGS_AFTER_PHASE_B1.txt`

---

## Update: APP Router Slice E.1 (2026-06-10)

| Cluster | Status |
|---------|--------|
| `/health`, `/api/version` in `app.py` | **extrahiert** → `api/routes/health.py`, `version.py` |
| Liveness payload | **reuse** `core.liveness` (kein Duplikat) |
| Version gate payload | **reuse** `runtime_governance.service` + `core.liveness` |

Evidence: `docs/evidence/app-monolith/APP_ROUTER_SLICE_E1.md`, `BOUNDARY_WARNINGS_E1.txt`

---

## Update: APP Router Slice E.2 (2026-06-10)

| Cluster | Status |
|---------|--------|
| Settings/Status GET in `app.py` | **extrahiert** → `settings.py`, `status.py` |
| Notification settings read | **reuse** `core.notification_settings` |
| Presets list | **reuse** `presets` module |

Evidence: `APP_ROUTER_SLICE_E2.md`, `BOUNDARY_WARNINGS_E2.txt`

---

## Update: APP Router Slice E.3 (2026-06-10)

| Cluster | Status |
|---------|--------|
| DCC capability/compact GET | **extrahiert** → `capabilities.py` |
| App catalog GET | **extrahiert** → `catalog.py` |
| logs/tail, self-update/status | **extrahiert** → `health.py`, `status.py` |

Evidence: `APP_ROUTER_SLICE_E3.md`, `BOUNDARY_WARNINGS_E3.txt`

---

## Update: APP Router Slice E.4 (2026-06-10)

| Cluster | Status |
|---------|--------|
| DCC modules/evidence index in `app.py` | **extrahiert** → `dev_dashboard_readonly.py` |
| Dateiscanner | **reuse** `core.dev_dashboard*` (kein Router-Duplikat) |

Evidence: `APP_ROUTER_SLICE_E4.md`, `BOUNDARY_WARNINGS_E4.txt`

---

## Update: APP Router Slice E.5 (2026-06-10)

| Cluster | Status |
|---------|--------|
| Roadmap registry slices in `app.py` | **extrahiert** → `dev_dashboard_roadmap.py` |
| Roadmap parser | **reuse** `core.dev_dashboard_roadmap.load_roadmap_registry_bundle` |

Evidence: `APP_ROUTER_SLICE_E5.md`, `BOUNDARY_WARNINGS_E5.txt`

---

## Update: APP Router Slice E.6 (2026-06-10)

| Cluster | Status |
|---------|--------|
| Roadmap next-prompts/export in `app.py` | **extrahiert** → `dev_dashboard_roadmap.py` |
| Export text | **reuse** `export_next_prompt_text` |

Evidence: `APP_ROUTER_SLICE_E6.md`, `BOUNDARY_WARNINGS_E6.txt`

---

## Update: Deploy Runner Registry C.1 (2026-06-10)

| Cluster | Status |
|---------|--------|
| 115 `runner_*.py` ohne einheitliche Metadaten | **C.1** — statische Registry `runner_registry.py` |
| Deploy-Runner Duplikat-Cluster (Rescue Build, Evidence) | inventarisiert in `DEPLOY_RUNNER_INVENTORY.md` — **nicht** dedupliziert |
| Runner-Ausführung / subprocess | unverändert — kein Refactoring in C.1 |

**C.2 (erledigt):** `runner_result_contract.py` — einheitliches `RunnerResult`-Schema, Legacy-Normalizer.

**C.3 (erledigt):** `runner_api_facade.py` — read-only Catalog/Summary/Empty-Result.

**C.4 (erledigt):** `runner_risk_gate.py` — Policy-Entscheidungen, Execute gesperrt.

**C.5+C.6 (erledigt):** 9 plan-only Routen decoupled.

**D.2 (erledigt):** Registry-Router `routes_registry.py` (5 GET).

**D.3 (erledigt):** Risk-Gate-Router `routes_risk_gate.py` (5 GET).

**D.4 (erledigt):** Evidence-Router `routes_evidence.py` (6 POST plan-only).

**D.5 (erledigt):** Governance-Router `routes_governance.py` (3 POST C.5).

**D.9 (übersprungen):** keine Notification-Routen — routes.py unverändert.

**M.1 (erledigt):** Modul-Katalog + Function Ownership Matrix + Do-Not-Duplicate Rules — kein Code-Refactoring.

**D.10 (erledigt):** `routes_versioning.py` — 8 plan-only Routen, facade_decoupling_d10.

**D.11 (erledigt):** `routes_runtime.py` — 8 read-only/status Routen.

**Nächster Schritt:** E.1 app.py Router-Slice (mit [Module Reuse Header](../../developer/CURSOR_PROMPT_MODULE_REUSE_HEADER.md))
