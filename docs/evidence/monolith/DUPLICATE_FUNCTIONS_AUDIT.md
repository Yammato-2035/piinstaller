# Duplicate-Functions-Audit — Themenübergreifende Doppelungen

**Datum:** 2026-06-16  
**Quellen:** `duplicate_scan_backend.txt`, `duplicate_keyword_scan.txt`, Importgraph, Modul-Inventar  
**Entscheidungsvokabular:** `keep` | `wrap_with_facade` | `extract_later` | `tests_first` | `private_only` | `public_safe_contract_only` | `blocked` | `unclear`

| Thema | Primäre Dateien | Sekundäre / Legacy-Duplikate | Entscheidung | Begründung |
|-------|-----------------|------------------------------|--------------|------------|
| **Storage Discovery** | `backend/core/storage_discovery.py` (276 Z.), `backend/core/storage_facade.py` (623 Z.) | `backend/modules/storage_detection.py` (lsblk/blkid/findmnt), `backend/app.py` (9× direkte Discovery-Imports), `backend/deploy/runner_rescue_storage_discovery.py` | **wrap_with_facade** | Facade ist dokumentierte kanonische Oberfläche; Legacy-Modul und `app.py`-Direktaufrufe parallel |
| **Mount Logic** | `storage_discovery.discover_findmnt_mounts_flat`, `discover_mounts` | `modules/storage_detection.py`, `core/backup_target_auto_prepare.py`, `core/safe_device.resolve_mount_source_for_path`, `recovery/*_execute._safe_under_target` | **extract_later** | findmnt/lsblk-Flattening an mehreren Stellen; Recovery-Pfad-Helfer dupliziert (`activation_execute` / `minimal_execute`) |
| **Write Guard** | `backend/safety/write_guard.py` (261 Z.) | `backend/deploy/real_write_guard.py` (Deploy-spezifisch), `backend/core/partition_storage_facade._write_guard_to_classification` | **wrap_with_facade** | `safety_facade` delegiert bereits; Deploy-Real-Write-Guard ist separater Session-Guard |
| **Safe Device** | `backend/core/safe_device.py` (993 Z.) | `safety_facade` (Legacy-Wrapper), `modules/storage_detection.validate_write_target`-Re-Export, `app.py` (4×) | **wrap_with_facade** | Fan-in ~13; Facade-Freeze in `safety_facade` dokumentiert — direkte Imports abbauen |
| **Backup Target Check** | `backend/core/backup_target_service_access.py` | `core/backup_target_auto_prepare.py`, `core/backup_readonly_handlers.backup_targets`, `api/routes/backup_readonly.py`, `app.validate_backup_target` (gepatcht in Tests) | **tests_first** | Mehrere Entry-Points für dasselbe Diagnose-ID-Schema (`BACKUP-TARGET-*`); Konsolidierung nach Contract-Tests |
| **Manifest** | `backend/core/deploy_manifest.py` (378 Z.), `backend/core/profile_deploy_manifest.py` (290 Z.) | `debug/support_bundle.py` (Bundle-Manifest), `api/routes/version.py` (`manifest_sha256`), `tools/generate_deploy_manifest.py` | **keep** | Unterschiedliche Manifest-Typen (Deploy vs. Profil vs. Support-Bundle); SHA-Helfer geteilt |
| **SHA256** | `deploy_manifest.manifest_sha256`, `core/windows_rescue_inspect.sha256_canonical_json` | `debug/support_bundle` (content_hash), `deploy/hardware_gate.py`, Rescue-Runner (ISO/Stick-Verify) | **public_safe_contract_only** | Hash-Helfer nicht vereinheitlichen ohne Rescue/Deploy-Evidence-Break; Vertrag in Tests festhalten |
| **Verify** | `backend/core/deploy_runtime_verify.py`, `backend/tools/verify_deploy_to_opt.py` | `modules/backup_verify.py`, `core/rescue_fat32_esp_usb_verify.py`, diverse `runner_*_verify` | **extract_later** | Domänengetrennte Verify (Deploy/Backup/Rescue); gemeinsame Result-Envelope später |
| **Runtime Gate** | `scripts/check-runtime-deploy-gate.sh`, `scripts/check-backend-version-gate.sh` | `backend/core/runtime_ports.py`, `core/dev_dashboard_cockpit` (Gate-Status), `tests/test_runtime_deploy_gate_eval_v1.py` | **keep** | Shell-Gates = Phase-0-Source-of-Truth; Backend spiegelt nur Status |
| **Deploy Drift** | `backend/core/profile_deploy_manifest.py`, `backend/core/deploy_manifest.py` | `core/dev_dashboard.py`, `core/dev_dashboard_cockpit.py`, `core/dcc_status_facade.py`, `core/dev_control_center_summary.py` | **wrap_with_facade** | Drift-Berechnung mehrfach aggregiert; `dcc_status_facade` als Read-only-Sammelpunkt |
| **Diagnostics Finding** | `backend/core/diagnostics/runner.py`, `core/diagnostics/models.py`, `core/diagnostics/registry.py` | `backend/diagnosis/interpret_v1.py`, `modules/storage_detection` (Diagnose-IDs), `safe_device` (`STORAGE-PROTECTION-*`), `backup_target_service_access` | **tests_first** | Zwei Pfade: strukturierte Diagnostics-API vs. verstreute String-IDs; Matcher-Tests (`test_diagnostics_matcher_hw1_*`) vor Merge |
| **Notification Events** | `backend/core/notification_events.py` (232 Z.) | `core/notification_state.py`, `core/notification_email.py`, `core/dcc_status_facade.py`, `app.py` | **keep** | Event-Contract mit dedizierten Tests (`test_notification_event_contract_v1`); E-Mail ist separater Kanal |
| **Auth / API-Key** | `backend/core/auth.py` (123 Z.) | `api/routes/ws.py` (`validate_session_token`), `core/fleet_session_state.py`, `devserver_agent/rescue_profile.py`, `rescue_remote/service.py` (Pairing-Token) | **public_safe_contract_only** | Session-Token vs. Rescue-Pairing vs. Fleet — unterschiedliche Threat-Models; nicht zusammenlegen |
| **Tokenprüfung** | `auth.validate_session_token` | `rescue_telemetry_ingest` (HMAC/Auth-Header), `rescue_remote` (`mask_token`), `debug/context.py` (request_id token) | **keep** | Homonym „token“; semantisch verschiedene Zwecke |
| **Redaction / Sanitizer** | `backend/core/redaction_contract.py` (92 Z., public-safe) | `backend/debug/redaction.py` (90 Z.), `rescue_remote/service.redact_text`, `core/rescue_telemetry_spool.py`, `debug/support_bundle.py` | **public_safe_contract_only** | `redaction_contract` = exportierbarer Vertrag; `debug/redaction` = Runtime-Logger; Rescue-Redaction eigene Patterns |
| **Telemetry Event Model** | `backend/core/rescue_telemetry_ingest.py` (~454 Z.) | `backend/rescue_telemetry/routers.py`, `core/rescue_telemetry_spool.py`, `core/rescue_telemetry_tasks.py` | **private_only** | Lokaler Dev-Ingest (`RESCUE_TELEMETRY_INGEST_ENABLED`); **kein** öffentlicher Telemetrie-Server |
| **Audit Log** | `backend/storage/db.py`, `backend/models/audit.py` | `app.py` (direkte Audit-Schreibpfade), `api/routes/sessions.py`, `modules/security.py`, `core/system_status_core.py` | **extract_later** | Audit-Persistenz zentral; Schreiblogik noch in `app.py` verstreut |
| **Rate Limit** | `backend/app.py` (slowapi) | `backend/modules/mail.py` (Provider-Limit) | **keep** | HTTP-Rate-Limit vs. E-Mail-Provider-Quota — verschiedene Ebenen |
| **API Client** | `frontend/src/api.ts` (244 Z.) | `frontend/src/api/*.ts` (partition, diagnostics, devDashboard, fleetSessions, …), vereinzelte `fetchApi` in Komponenten (`PartitionWorkbenchShell`) | **wrap_with_facade** | Zentrale `fetchApi` existiert; Sub-APIs sind dünn — direkte Fetches in Komponenten vermeiden |
| **Status Mapping** | `frontend/src/viewmodels/statusViewModel.ts` (510 Z.) | `frontend/src/trafficLight/trafficLightModel.ts`, `lib/devDashboard/buildStandaloneDashboard.ts`, `config/riskLevels.ts`, Backend `core/dcc_status_facade.py` | **keep** | Frontend-ViewModel vs. Backend-Status-Facade — bewusst getrennte Schichten; Duplikat nur in Ampel-Farblogik (Tests: `statusComponentMigrationH*`) |
| **i18n Keys** | `frontend/src/locales/de.json`, `en.json` (je 3.379 Z.) | `backend/core/backup_recovery_i18n.py` (Backend-String-Keys für Diagnosen) | **unclear** | Parallele Key-Räume Backend/Frontend; keine automatische Konsistenzprüfung — später `extract_later` mit gemeinsamem Key-Katalog |

## Cluster mit höchster Konsolidierungsrendite

1. **Storage + Safety** (`storage_discovery` → `storage_facade`; `safe_device`/`write_guard` → `safety_facade`) — reduziert `app.py`-Fan-out.
2. **Deploy Drift + DCC Status** — ein Read-model über `dcc_status_facade`.
3. **Redaction** — `redaction_contract` als einzige public dokumentierte Oberfläche; interne Implementierungen nicht mergen ohne Rescue-/Debug-Regression.
4. **Backup Target** — ein Diagnose-ID-Schema, mehrere Handler; `tests_first` vor API-Vereinheitlichung.

## Explizit nicht zusammenlegen

| Paar | Grund |
|------|-------|
| `rescue_telemetry_ingest` ↔ Produkt-Telemetrie | Lokaler Lab-Ingest, opt-in per Env — kein Cloud-Telemetry-Server |
| `real_write_guard` ↔ `write_guard` | Deploy-Session-Guard vs. generische Write-Safety |
| `deploy_manifest` ↔ Support-Bundle-Manifest | Unterschiedliche Lifecycle und Consumer |

## Evidence-Querverweise

- `docs/evidence/monolith/duplicate_scan_backend.txt` — Funktionsnamen-Duplikate (inkl. Recovery `_safe_under_target`)
- `docs/evidence/monolith/duplicate_keyword_scan.txt` — thematische Treffer (redaction, manifest, diagnostics)
- `backend/core/safety_facade.py` — dokumentierter Facade-Freeze
- `backend/core/redaction_contract.py` — Public-safe Redaction-Vertrag
