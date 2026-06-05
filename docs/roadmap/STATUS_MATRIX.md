# Setuphelfer – Statusmatrix (Ampel)

**Stand:** 2026-05-26 — **BR-001-Pivot:** **BR-001-LIVE** experimentell/rot (kein Release-Gate, keine Live-Desktop-Gate-Retries). **BR-001-OFFLINE** (Rettungsstick) = **Release-Gate** (rot bis HW-E2E). **PKG-001**, **DEV-001**, **BR-011–BR-019** wie zuvor. **BR-004/005:** blocked an **BR-001-OFFLINE**-Archiv. Siehe `docs/architecture/BR-001_GATE_STRATEGY_DE.md`.

## Ampeldefinition

| Ampel   | Bedeutung |
|---------|-----------|
| Grün    | umgesetzt, getestet, dokumentiert, reproduzierbar, Evidence vorhanden |
| Gelb    | teilweise umgesetzt oder vorbereitet, noch nicht vollständig validiert |
| Rot     | geplant, offen oder fehlerhaft, keine belastbare Abnahme |
| Schwarz | bewusst geparkt, nicht Teil dieser Arbeitsphase |

## Gesamtüberblick

| Bereich | Ampel | Kurzinfo | Evidence / Anker |
|---------|-------|----------|------------------|
| Phase 0 Arbeitsmodus | Gelb | Struktur & Matrizen angelegt, GitHub Project manuell | `docs/evidence/release-gates/feature_freeze.json` |
| Phase 1 Bestandsaufnahme | Gelb | Testinventar + **Pytest Snapshot** (0× fail, 1526× pass, lokal); CI-/HW-Evidence separat | `test_inventory.json`, `current_failures.json`, `pytest_failures_summary_2026-05-11.txt` |
| Backup / BR-001-OFFLINE | Rot | Release-Gate: Rettungsstick Full-Backup HW offen — **`BR-001_offline_gate_pivot_2026-05-20.md`** | `RESCUE_STICK_TEST_MATRIX.md`, `BR-001_GATE_STRATEGY_DE.md` |
| BR-001-LIVE (Desktop) | Rot | Experimentell — Live tar/Chrome/Timeshift/apt; **kein** Release-Retry | `BR-001-full-root-stable-pigz-timeshift-retry-2026-05-20.json` |
| Backup Preflight **BR-011** | Gelb | Spezifikation + Testmatrix; API/UI/Implementierung offen | `docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md`, `docs/knowledge-base/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT.md` |
| **BR-013** Ziel-Schreib-EIO | Gelb | `backup.write_io_error` + pytest; KB `BACKUP_TARGET_WRITE_IO_ERROR.md` | `BR-001_write_io_error_2026-05-14.md`, `backup_runner.py`, `BR-001.json` |
| **BR-012** Runner-Finalisierung | Gelb | Fix `backup_runner.py` + pytest; **2026-05-14** produktiver Runner SHA256 = Workspace (Deploy-Prep) | `BR-001_runner_finalization_performance_failure_2026-05-14.md`, `backend/tools/backup_runner.py`, `BR-001.json` → `br001_runner_fix_deploy_prep_2026_05_14` |
| **BR-016** Backup Performance / Kompression | Gelb | pigz wenn verfügbar; Profile-Excludes; zstd vorbereitet; Doku `BACKUP_PERFORMANCE_*` | `test_backup_archive_options_v1.py`, `core/backup_archive_options.py` |
| **BR-017** Backup Evidence Collector | Gelb | `tools/backup_evidence_collector.py`; Runner-Hook; fehlende Rechte → `permission_denied` | `test_backup_evidence_collector_v1.py`, `BACKUP_EVIDENCE_COLLECTOR_DE.md` |
| **BR-018** Backup Progress / ETA | Gelb | UI: `BackupJobProgressSection` + Modal/Page; API Evidence `GET`/`POST`; ETA ohne Total = i18n „unbekannt“ | `BACKUP_PERFORMANCE_DE.md`, `test_backup_job_evidence_api_v1.py`, Vitest `backupJobProgressDisplay.test.ts` |
| **BR-019** Backup Profiles | Gelb | API-Liste/Preview, Create-Vertrag, UI-Standard **recommended**, Full-Expert nur mit Checkbox; pytest `test_backup_profiles_v1` + Vitest `backupCreateBody.test.ts`; HW-Abnahme Daten-Scope offen | `docs/backup/BACKUP_PROFILES_DE.md`, `BACKUP_PROFILES_EN.md`, `docs/knowledge-base/backup/BACKUP_PROFILES.md` |
| Verify | Rot | BR-004/BR-005 blocked — kein neues BR-001-Archiv aus diesem Lauf | `BR-004.json`, `BR-005.json` |
| Restore | Rot | kontrollierte HW-Abnahmen ausstehend | `docs/evidence/backup-restore/` |
| Hardwaretests | Rot | Matrix vorbereitet | `docs/testing/HARDWARE_TEST_MATRIX.md`, `docs/evidence/hardware/` |
| Rescue Stick | Rot | BR-001-OFFLINE Release-Gate; Deploy-Pipelines teilweise; RS-001–008 HW rot | `RESCUE_STICK_TEST_MATRIX.md`, `rescue-stick.json` |
| Monolith-Audit | Gelb | App-Bootstrap extrahiert (`app_bootstrap/`); `app.py` noch ~17k Zeilen; Boundary `review_required` | `docs/evidence/monolith/APP_PY_AFTER_DECOMPOSITION.md`, `docs/architecture/APP_BOOTSTRAP_ARCHITECTURE.md` |
| **App.py Bootstrap / Decomposition** | **Gelb** | Factory, Middleware-, Router-Registry, Startup-Diagnostik, Dev-Dashboard-Service; **kein** Deploy; Live-Diagnose nach Sync | `docs/evidence/runtime-results/app_decomposition_before_rescue_iso_gate.json`, `docs/evidence/rescue/RESCUE_ISO_BUILD_READINESS_AFTER_APP_DECOMPOSITION.md` |
| Website-Transparenz | Gelb | Markdown-Basis im Repo | `docs/roadmap/PUBLIC_STATUS_PAGE.md`, `docs/testing/WEBSITE_TRANSPARENCY_TEST_MATRIX.md` |
| Affiliate / Monetarisierung | Gelb | Policies als Markdown | `docs/monetization/` |
| Release Gate UG-Start | Rot | Gates nicht grün | `docs/roadmap/RELEASE_READINESS_CHECKLIST.md` |
| Development Cockpit **DEV-001** | Grün | Deploy-Drift-False-Positive behoben (`2c7e9ee`); Helper-Deploy abgenommen: Gate Exit `0`, `deploy_drift=green`; Rescue-ISO **gelb** (Build/Policy, nicht Deploy-Drift); `usb_write.allowed=false` | `docs/evidence/dev-dashboard/DEPLOY_DRIFT_SINGLE_FILE_FIX.md`, `docs/evidence/dev-dashboard/DEPLOY_HELPER_INTEGRATION_RESULT.md`, `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md` |
| **Notification Dashboard** | Grün | Produktive Runtime verifiziert: Dashboard-Events bleiben gruen sichtbar und persistieren unter `/var/lib/setuphelfer/notifications`, auch wenn der E-Mail-Pfad wegen Provider-Limit gelb ist | `NOTIFICATION_MODULE_IST_ANALYSIS.md`, `NOTIFICATION_MODULE_INTEGRATION_RESULT.md`, `NOTIFICATION_EVENT_CONTRACT.md`, `/var/lib/setuphelfer/notifications/notification_latest_summary.json` |
| **Notification Email** | Gelb | Dashboard-Status bleibt produktiv gelb, weil das persistierte Rescue-Failure-Event sauber als `notification.email.provider_limit_exceeded` klassifiziert ist (`554 5.7.0 outgoing message limit exceeded`, `next_action=check_smtp_provider_limit_or_wait`, kein Fake-Gruen); separater aktueller Test-Mail-Smoke antwortete zwar mit `sent`, hebt den persistierten Failure-Status aber nicht rueckwirkend auf | `NOTIFICATION_MODULE_INTEGRATION_RESULT.md`, `NOTIFICATION_EMAIL_SETUP_RUNBOOK.md`, `/var/lib/setuphelfer/notifications/notification_events.jsonl`, `/var/lib/setuphelfer/notifications/notification_latest_summary.json` |
| Backend-Version-Gate | Grün | Regel+Skript+`/api/version`-Diagnose im Repo; produktiver Runtime-Gate-Lauf auf `/opt/setuphelfer` liefert Exit `0` | `docs/evidence/release-gates/backend_version_update_gate.json`, `scripts/check-backend-version-gate.sh`, `docs/evidence/dev-dashboard/DEPLOY_HELPER_INTEGRATION_RESULT.md` |
| **PKG-001** Runtime-Paket-Deploy-Gate | Gelb | Packaging-Readiness ist read-only produktiv sichtbar (`deb`/`rpm`/`AppImage` vorhanden), aber Installationsabnahme bleibt pending; kein fake install green | `docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md`, `PACKAGE_DEPLOYMENT_GATE_EN.md`, `scripts/check-runtime-deploy-gate.sh`, `scripts/runtime_deploy_gate_eval.py`, `docs/evidence/release-gates/apt_update_delivery_gap.json`, `docs/evidence/dev-dashboard/PROJECT_OVERVIEW_DASHBOARD_INTEGRATION_RESULT.md` |
| Cloudserver Edition | Schwarz | nach Modularisierung | — |
| **Partitions Phase 2 UI Preview Stub** | Grün | Offizieller `deploy-to-opt` (2026-05-24); Gate Exit 0; API-Smoke read-only; UI-Bundle `index-B-1eLB5j.js` aus Deploy; Browser-Checkliste `?page=partitions` | `docs/evidence/partitions/PARTITIONS_PHASE2_UI_PREVIEW_STUB.md` |
| **Rescue stick read-only build emulation** | Grün | Regression lokal grün; verbotene Live-Build-Altartefakte aus dem Build-Tree bereinigt; dokumentierte Forbidden-Tokens bleiben nur Review-/Doku-Kontext | `RESCUE_STICK_READONLY_BUILD_EMULATION.md`, `RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md` |
| **Rescue stick temp runtime bundle** | Grün | `create-temp-runtime-bundle.sh` + Validator Exit 0; MANIFEST lokal | `RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md` |
| **Rescue stick temp runtime prep** | Grün | Skripte, Runbooks, Copy-Handoff | `scripts/rescue-live/` |
| **Rescue stick Live-OS network validation** | Gelb | Session 3: Bundle ok; USB-Copy VFAT/symlinks; **kein Live-Boot** | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` |
| **Controlled ISO build prep (live-build tree)** | Grün | Tree + Bundle Validator Exit 0 | `RESCUE_CONTROLLED_ISO_BUILD_PREP_RESULT.md` |
| **Controlled ISO build precheck (no build)** | Grün | Cleanup ok; Validate Exit 0; Operator-Build freigegeben | `controlled_iso_build_precheck_latest.json` |
| **Controlled ISO build (2026-06-02)** | Gelb | LB_EXIT=0; Artefakt ok; Squashfs-Validator 0; **kein Boot/USB** | `CONTROLLED_RESCUE_ISO_BUILD_RESULT.md` |
| **QEMU Guest Agent Smoke** | Rot / blocked | `guest_rescue_venv_glibc_mismatch` — Run `143148`: SEND ok; **GLIBC_2.38** Gast-venv; kein Guest-Report | `QEMU_143148_FAILURE_CLASSIFICATION.md`, `RESCUE_QEMU_RECURRENT_FAILURES.md` |
| **Runtime Governance** | Gelb | `ready_for_operator_deploy_validation` — nach Deploy release/local_lab-Parity live prüfen | `RUNTIME_GOVERNANCE_DELEGATION_RESULT.md` |
| **DCC unter release** | Grün (expected) | Dev-Routen `PROFILE_ROUTE_BLOCKED`; Ports ok — kein Portfehler | `DCC_LIVE_ACCEPTANCE_RELEASE_BASELINE.md` |
| **DCC unter local_lab live** | **Grün** | local_lab API 200 + Operator-DCC sichtbar; release restore belegt | `DCC_LIVE_ACCEPTANCE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md`, `DCC_RELEASE_RESTORE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md` |
| **DCC Frontend Profile Desync (Gating)** | **Grün** | Gating deployed; local_lab + release restore live belegt | `DCC_FRONTEND_PROFILE_DESYNC_RESULT.md`, `DCC_RELEASE_RESTORE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md` |
| **DCC Blank Screen Fail-Safe** | **Grün** | `blank_dcc_screen` resolved; local_lab + release Disabled+Diagnose sichtbar | `DCC_BLANK_SCREEN_TRIAGE_RESULT.md`, `DCC_RELEASE_RESTORE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md` |
| **Windows Laptop Rescue Inspect** | Gelb | P1 Track `windows-laptop-rescue-inspect`; Schema+Codes+KB; read-only MVP planning | `WINDOWS_LAPTOP_RESCUE_INSPECT_PLAN.md`, `windows_inspect.schema.json` |
| **DCC Roadmap Output Filter** | Gelb | Kurzüberblick+Filter+Roh-JSON collapsible; kein ungefilterter Dump in Hauptansicht | `RoadmapDrawer.tsx`, `roadmapFilter.ts` |
| **Roadmap-First / KB-First Governance** | Gelb | Regeln in `CURSOR_WORK_RULES.md` + `.cursor/rules/200_ROADMAP_KB_FIRST.md`; Known-Error-Triage-Template; recurrent-errors KB | `PROJECT_RULES_ROADMAP_KB_FIRST_RESULT.md`, `project_rules_roadmap_kb_first_latest.json` |
| **Known Error Triage (Evidence)** | Gelb | `new_governance_required` — Pflicht: KB-Suche vor jedem Fix | `KNOWN_RECURRENT_ERRORS.md`, `known_error_triage.schema.json` |
| **Developer QEMU ISO Rebuild** | Grün | Operator `rescue_developer_iso_20260602_220129` LB_EXIT=0; SHA `614cc86e…`; Autopilot wants in Squashfs; ready for smoke | `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_SUCCESS_INGEST_RESULT.md` |
| **Controlled ISO build execution** | Grün | Developer controlled build `rescue_developer_iso_20260531_103047` — LB_EXIT=0, summary success, permission clean after 8455e3c | `RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`, `controlled_iso_build_latest_summary.json` |
| **Rescue ISO artifact** | Grün | Developer ISO `binary.hybrid.iso` (509607936 B), SHA256 `52da3e018ccb…`; unterscheidet sich von archivierter Prior-ISO | `rescue_developer_iso_latest.sha256`, `rescue_developer_controlled_iso_build_result.json` |
| **Rescue Developer Profile + Dev Agent** | Grün | Developer profile validiert; Public auto-upload blockiert; Guard Exit 0 (`8e07acf`) | `docs/evidence/dev-server/DEV_AGENT_RESCUE_PROFILE_INTEGRATION.md`, `build/rescue/profiles/developer/` |
| **Rescue Developer ISO Dry-Build** | Gelb | Dry-Build Manifest `review_required` — prior ISO artifacts in tree (33), keine neuen Artefakte; Profile/Guard OK | `rescue_developer_iso_dry_build_manifest.json`, `RESCUE_DEVELOPER_ISO_DRY_BUILD_RESULT.md` |
| **Rescue Developer Controlled ISO Build** | Grün | LB_EXIT=0, ISO+SHA256, developer agent in chroot, public guard OK; permission clean nach 8455e3c | `RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`, `rescue_developer_controlled_iso_build_result.json` |
| **Real Developer ISO Build** | Grün | Controlled build success run `103047`; kein USB | `controlled_iso_build_latest_summary.json` |
| **Fleet Session Phase 1 Backend Runtime** | **Grün** | Live-Abnahme gegen `/opt` abgeschlossen: `local_lab` aktiv, Fleet-API live erreichbar, manueller Host-Session-Smoke durchgeführt, danach Rückschaltung auf `release` mit Gate grün | `FLEET_SESSION_PHASE1_RESULT.md`, `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session API Smoke** | **Grün** | Genau ein manueller Live-Smoke ohne QEMU durchgeführt (create+finish+final read/persistenz), Release-Probes danach korrekt `HTTP 404 PROFILE_ROUTE_BLOCKED` | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session Persistence** | **Grün** | Persistenz des manuellen Runs unter Runtime-Pfad `/opt/setuphelfer/docs/evidence/runtime-results/dev-dashboard/fleet_sessions*.json*` nachgewiesen | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session Timeout Semantics** | **Grün** | Finalstatus `timeout` mit `qemu.exit_code=124` und Finding `qemu_timeout_124` live belegt | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session serial_empty Semantics** | **Grün** | `serial.size_bytes=0` und Finding `serial_empty` live sichtbar | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session guest_report_missing Semantics** | **Grün** | `guest.report_seen=false`, `dev_server_report_new=false` und Finding `guest_report_missing` live sichtbar | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fake VM Prevention** | **Grün** | Kein QEMU-Lauf, keine Fake-VM, kein Gast-Knoten ohne Ingest erzeugt | `FLEET_SESSION_PHASE1_LIVE_ACCEPTANCE_RESULT.md` |
| **Fleet Session QEMU Wrapper JSON Payload** | **Grün** | ENV+Heredoc Payloads; Shell-Test + API smoke OK | `FLEET_SESSION_QEMU_WRAPPER_JSON_FIX_RESULT.md` |
| **Fleet Session UI (Cockpit)** | **Grün** | Telemetry-Kachel `Lab Sessions` inkl. LED/KVM/Serial/Guest-Status implementiert | `FLEET_SESSION_PHASE1_RESULT.md` |
| **Dev Diagnostic Export Backend** | **Grün** | Implementiert + pytest; `/api/dev-diagnostics/*` | `DEV_DIAGNOSTIC_EXPORT_RESULT.md` |
| **Dev Diagnostic Export Live API** | **Grün** | Live auf `127.0.0.1:8000` (Export `081222`) | `DEV_DIAGNOSTIC_EXPORT_LIVE_ACCEPTANCE_RESULT.md` |
| **Dev Diagnostic Export UI** | **Gelb** | Copy-Buttons in Source/dist; Browser optional | `DEV_DIAGNOSTIC_EXPORT_DE.md` |
| **QEMU Smoke 081222 Export** | **Grün** | `serial_empty_boot_unknown`, serial=0, report_new=false | `QEMU_DEVELOPER_SMOKE_20260601_081222_ANALYSIS.md` |
| **Rescue Developer Serial Config** | **Grün** | Prepare `developer-qemu` materialisiert (tty0+ttyS0, kein quiet/splash) | `RESCUE_ISO_SERIAL_BOOT_VISIBILITY_FIX_RESULT.md` |
| **Rescue Developer ISO Rebuild** | **Grün** | Vorheriger Lauf: LB_EXIT=0; ISO SHA `be016f2a…` (vs. `6a44d1fe…`) — **ohne** Commit `2e0216f` Bootloader-Serial | `RESCUE_DEVELOPER_ISO_SERIAL_VISIBILITY_BUILD_RESULT.md` |
| **Rescue Developer ISO Rebuild after Bootloader Fix** | **Grün** | Operator-Build `LB_EXIT=0`; neue SHA `5c79e35c…` (vs. `be016f2a…`); ISOLINUX SERIAL im ISO | `RESCUE_DEVELOPER_ISO_BOOTLOADER_SERIAL_CAPTURE_BUILD_RESULT.md` |
| **Bootloader Serial Static Validation** | **Grün** | SERIAL/TIMEOUT/live- + tty0/ttyS0 im Tree und ISO; Marker gelb (Squashfs) | `RESCUE_DEVELOPER_ISO_BOOTLOADER_SERIAL_CAPTURE_STATIC_VALIDATION.md` |
| **Static ISO Serial Validation** | **Grün** | tty0+ttyS0+loglevel im ISO; Marker gelb (Squashfs), Tree grün | `RESCUE_DEVELOPER_ISO_STATIC_SERIAL_VALIDATION.md` |
| **Serial Visibility Runtime** | **Grün** | Smoke `202000`: serial **132412** B; ISOLINUX+Kernel+systemd sichtbar | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| **QEMU Bootloader Serial Smoke** | **Grün** | Ein Lauf; chardev+isa-serial; nicht mehr 0 Bytes | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| **Autopilot Serial Markers** | **Grün** | Boot/Autopilot/Agent-Marker im `developer-qemu`-Profil | `RESCUE_DEVELOPER_SERIAL_VISIBILITY_CONTRACT.md` |
| **Fleet Finish Telemetry** | **Grün** | Finish-Payload: exit_code, serial.path, kvm/acceleration | `FLEET_SESSION_QEMU_FINISH_TELEMETRY_FIX_RESULT.md` |
| **Serial Visibility (Rescue QEMU)** | **Gelb** | ISO-Cmdline neu; Runtime-Serial noch offen bis Smoke | `RESCUE_DEVELOPER_ISO_STATIC_SERIAL_VALIDATION.md` |
| **QEMU Serial Device Capture** | **Grün** | Wrapper: chardev+isa-serial Default, prepare_serial_log | `QEMU_SERIAL_CAPTURE_AND_BOOTLOADER_OUTPUT_FIX_RESULT.md` |
| **Bootloader Serial Output** | **Grün** | ISOLINUX SERIAL/TIMEOUT/live- im ISO nach Operator-Rebuild | `RESCUE_DEVELOPER_ISO_BOOTLOADER_SERIAL_CAPTURE_STATIC_VALIDATION.md` |
| **QEMU Smoke Serial Retry** | **Rot** | Lauf `160824` vor Fix; nächster Smoke nach ISO-Rebuild | `QEMU_DEVELOPER_SMOKE_SERIAL_VISIBILITY_RETRY_RESULT.md` |
| **QEMU Smoke Retry** | **Grün** | Serial-Capture Mindestziel erfüllt (`202000`) | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| **QEMU Smoke Retry (gesamt)** | **Gelb** | Serial grün; API-Export/Autopilot/Ingest offen (release-Runtime) | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| **Rescue Remote Security Model** | **Grün** | Phase 1: keine Shell, allowlisted runbooks | `RESCUE_REMOTE_CONTROL_SECURITY_MODEL.md` |
| **Rescue Remote Agent Stub** | **Grün** | `setuphelfer-rescue-remote-agent.sh` + Backend API | `RESCUE_REMOTE_CONTROL_PHASE1_RESULT.md` |
| **Rescue Remote Job Queue** | **Grün** | JSONL `build/runtime/rescue-remote/` | oben |
| **Rescue Network Boot Menu Contract** | **Grün** | eth0/WLAN/QEMU-Lab/Pairing Konzept | `RESCUE_NETWORK_BOOT_MENU_CONTRACT.md` |
| **Rescue Network Menu Stub** | **Grün** | `setuphelfer-rescue-network-menu.sh` | oben |
| **Remote Shell** | **Disabled** | Keine API-Route | `RESCUE_REMOTE_CONTROL_SECURITY_MODEL.md` |
| **Remote Write Actions** | **Disabled** | `controlled_write` blockiert Phase 1 | oben |
| **Guest Autopilot** | **Gelb** | Boot OK; Units im ISO; Marker/Report fehlen (Timeout+release) | `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` |
| **Devserver Agent (QEMU)** | Gelb | Host Devserver bei `release` blockiert (erwartet); Preflight verhindert Smoke ohne `local_lab` | `QEMU_GUEST_AGENT_DEVSERVER_PREFLIGHT_ANALYSIS.md` |
| **Devserver Ingest (QEMU lab)** | Rot | `report_new=false` bis erfolgreicher Smoke mit aktivem Devserver | `DEVELOPER_QEMU_ISO_AFTER_AUTOPILOT_SUCCESS_INGEST_RESULT.md` |
| **Public Dev-Control Exposure** | **Grün** | Keine öffentlichen Dev-Control-Hosts in Produkt-Routen; lokal `:8000` | `DEV_DIAGNOSTIC_EXPORT_IST_ANALYSIS.md` |
| **QEMU Developer Smoke 081222** | **Rot** | Historisch: alte ISO, serial=0 | `QEMU_DEVELOPER_SMOKE_20260601_081222_ANALYSIS.md` |
| **QEMU Developer Smoke 160824** | **Rot** | Neue ISO, serial weiterhin 0 — Capture/Boot-Output-Fix nötig | `QEMU_DEVELOPER_SMOKE_SERIAL_VISIBILITY_RETRY_RESULT.md` |
| **QEMU Smoke with Session** | **Rot** | Wrapper JSON grün; Gast-Report + Serial offen — `qemu_smoke_next_step_allowed=false` bis Folgefix | oben |
| **Rescue Guest Report Ingest (QEMU lab)** | **Rot** | Lauf `081222`: `reports_last_24h` unverändert, kein neuer Knoten | `QEMU_DEVELOPER_SMOKE_20260601_081222_ANALYSIS.md` |
| **Proxy Bind Exposure (QEMU lab)** | **Gelb** | `0.0.0.0` nur via QEMU-Smoke + Operator-Confirm; Default `127.0.0.1`; lab-only NDA | `FLEET_SESSION_QEMU_WRAPPER_JSON_FIX_RESULT.md` |
| **Public Push (Fleet/Dev-Control)** | **Rot/Blocked** | `blocked_public_repository_ndA_risk` | — |
| **Install Profiles** | **Grün** | Release + Local-Lab live abgenommen; Default `release` | `INSTALL_PROFILES_AND_DEPLOY_SCOPES.md` |
| **Release Profile Live** | **Grün** | Nach Local-Lab wiederhergestellt; Profil-Gate Exit 0 | `PROFILE_LIVE_RELEASE_ACCEPTANCE_RESULT.md` |
| **Profile-aware Manifests** | **Grün** | `deploy/manifests/*.json`; Generator `--profile`; Drift V2 im Dashboard | `PROFILE_DEPLOY_DRIFT_V2_RESULT.md` |
| **Router Profile Gates** | **Grün** | Bedingte Router + Middleware; pytest 19/19 | `PROFILE_ROUTER_GATE_RESULT.md` |
| **Runtime Profile Deploy Gate** | **Grün** | Release-Live Exit 0; Retry nach Restart; unabhängig vom Legacy-Gate | `PROFILE_LIVE_RELEASE_ACCEPTANCE_RESULT.md` |
| **Release Dev Route Blocker** | **Grün** | HTTP 404 fleet/dev-diagnostics/rescue-remote/dev-dashboard/dev-server | oben |
| **Dev Server Release Blocker** | **Grün** | `/api/dev-server/health` 404; Override ignoriert | `RUNTIME_HTTP_000_AFTER_PROFILE_DEPLOY_ANALYSIS.md` |
| **Legacy Runtime Gate** | **Deprecated** | `LEGACY_GATE_NON_PROFILE_AWARE` — erfordert dev-dashboard 200 | `check-runtime-deploy-gate.sh` |
| **Frontend Bundle Hygiene** | **Gelb** | UI guarded; i18n-Strings im Bundle | `FRONTEND_PROFILE_BUNDLE_HYGIENE_NOTE.md` |
| **Profile-aware Deploy Drift** | **Grün** | `enrich_deploy_drift_profile_aware`; Gate Exit 16 entkoppelt bei `profile_manifest_match` | `PROFILE_DEPLOY_DRIFT_V2_RESULT.md` |
| **Frontend Profile Marker** | **Gelb** | UI-Gates release; i18n-Strings noch im Haupt-Bundle | `FRONTEND_PROFILE_BUILD_RESULT.md` |
| **Release Dev Route Blocker** | **Grün** | Release blockiert Fleet/Dev-Diag/Rescue-Remote/Dev-Dashboard | `test_install_profile_gate_v1.py` |
| **Local-Lab Dev Route Allowance** | **Grün** | TestClient: Fleet/Dev-Diag/Rescue-Remote/Dev-Dashboard erreichbar | `PROFILE_LIVE_LOCAL_LAB_ACCEPTANCE_RESULT.md` |
| **Local-Lab Profile Live** | **Grün** | Operator-sudo: Drop-in, `/api/version` local_lab, Profil-Gate Exit 0 | `PROFILE_LIVE_LOCAL_LAB_ACCEPTANCE_RESULT.md` |
| **Rescue Remote Local-Lab** | **Grün** | Live + TestClient: shell 403, read-only Job 200 | oben |
| **Runtime Final Profile** | **release** | Nach Abnahme Release-Drop-in wiederhergestellt | oben |
| **Public Exposure Gate** | **Grün** | Default `public_exposure_allowed=false`; Exit 21 bei 0.0.0.0 | `runtime_profile_deploy_gate_eval.py` |
| **Public Push** | **Blocked** | `blocked_public_repository_ndA_risk` | Repository visibility public |
| **Live Boot (Developer ISO)** | Gelb | Neues ISO gebaut; QEMU-Serial-Smoke als Nächstes | `RESCUE_DEVELOPER_ISO_SERIAL_VISIBILITY_BUILD_RESULT.md` |
| **USB Write** | Rot/Blocked | `usb_write.allowed=false` | Rescue safety gates |
| **Controlled ISO preparation** | Gelb | Workspace-Pfad bleibt gruen; Prebuild zeigt fehlende RSVG-Build-Abhaengigkeit jetzt vor dem Build sichtbar an, echter Build weiterhin nicht neu ausgefuehrt | `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md`, `RESCUE_ISO_RSVG_FAILURE_ANALYSIS.md` |
| **Rescue USB write gate** | Rot | **blocked** — kein ISO, keine Zielgeraet-Auswahl, keine Doppelbestaetigung, kein `dd`; neuer RSVG-Preflight haelt den Pfad weiterhin vor jedem USB-Folgeversuch an | `RESCUE_USB_WRITE_GATE_RUNBOOK.md`, `RESCUE_USB_WRITE_RESULT.md`, `controlled_usb_write_latest_summary.json` |
| **Rescue stick real ISO build** | Rot | **blocked** — `real_iso_build_allowed: false`; Live-OS **green** auf Hardware ausstehend | `RESCUE_STICK_READONLY_BUILD_GATE.md` |

## Phasen-ToDos (Kurz)

| Phase | Ampel | Nächster Schritt |
|-------|-------|------------------|
| P0 | Gelb | GitHub Project anlegen, Issues aus Matrizen |
| P1 | Gelb | Lokal dokumentiert; **GitHub-CI-Ergebnis** separat vergleichen und verlinken |
| P2 | Rot | BR-Tests auf Hardware ausführen, Evidence |
| P3 | Rot | HW-001ff. ausführen |
| P4 | Rot | Rescue Evidence RS-001ff. |
| P5 | Rot | Monolith-Scan aus Prompt 6 |
| P6–P8 | Rot / Gelb | Website, Affiliate, Release-Gates |

## Blocker-Raster (Prompt 2 – klassifiziert)

Vollständiges Inventar: **`docs/evidence/release-gates/blocker_inventory.json`** · Kurzbericht: **`docs/evidence/release-gates/prompt02_abschlussbericht.md`** · Cursor-Prompt: **`docs/cursor/PROMPT_02_BLOCKER_INVENTORY.md`**

### P0 (blockiert Backup/Restore/Hardwaretest)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P0-HW-E2E | Kein dokumentierter HW-Nachweis Backup→Verify→Restore→Boot | `HARDWARE_TEST_MATRIX.md` + `HW-*.json` |

### P1 (blockiert Rescue/Release-Vertrauen)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P1-PYTEST | Lokale Suite **grün** (0 failures, Snapshot 2026-05-11); **CI-Lauf in Evidence** weiterhin offen | `current_failures.json`, `blocker_inventory.json` → `pytest_local_followup` |
| P1-CI | GitHub CI rot (Run 25687412698); kein grüner Lauf | Fix13-Pytest vs. CI; danach erneuter Lauf, URL/Conclusion in `ci_evidence.json` |
| P1-RESCUE | Rescue-Stick / RS-* Evidence (Unit-Tests phase3 + Bundle lokal grün) | `RESCUE_STICK_TEST_MATRIX.md`, `docs/evidence/rescue-stick/` |

### P2 (Website/Transparenz/Recht)

| ID | Thema | Nächster Schritt |
|----|-------|------------------|
| P2-WEB | Live-Site vs. WT-* offen | Statusseite veröffentlichen, `github_status_link.json` |
| P2-LEGAL | Recht/Affiliate ohne Abnahme | `legal_release_gate.md` |

### P3 (später / niedriger)

| ID | Thema |
|----|-------|
| P3-DEBUG | Support-Bundle / Instrumentation (lokal grün; Priorität niedrig wenn Regression) |
| P3-MONOLITH | DOMAIN_BOUNDARIES-Stubs → Prompt 5 |
| P3-CLOUD | Cloudserver – **schwarz** |

### Legacy-Konflikt-Raster

| ID | Priorität | Thema | Status |
|----|-----------|-------|--------|
| B-LEGACY | P1 | pi-installer / PI_INSTALLER_* / npm-Name | `legacy_inventory.json` |
| B-PORTS | P2 | 8000 / 3001 / 5173 / 8010 (Rescue-Doku) | `runtime_inventory.json` |
| B-MOUNT | P2 | Mount/Permission/HW-Varianten | `storage_permission_inventory.json` |
| B-LEGAL | P2 | Impressum/Datenschutz/Affiliate | siehe P2-LEGAL |

*Pytest-Detail:* `docs/evidence/release-gates/current_failures.json` (enthält Verweis auf `blocker_inventory.json` über gemeinsames Release-Gate-Set).*

## Phasen-Checkliste (IDs aus Arbeitsplan)

### Phase 0 – Arbeitsmodus

| ID | Aufgabe | Status |
|----|---------|--------|
| P0-001 | Feature-Freeze | Erledigt (Evidence: `feature_freeze.json`, Ampel Gelb bis formale Abnahme) |
| P0-002 | Baustellen inventarisiert | Laufend (`STATUS_MATRIX`, Blocker) |
| P0-003 | Ampeldefinition im Repo | Erledigt (oben + `PUBLIC_STATUS_PAGE.md`) |
| P0-004 | Evidence-Struktur | Erledigt (`docs/evidence/README.md` + Unterordner) |
| P0-005 | GitHub Project-Felder | Doku erledigt (`GITHUB_PROJECT_SETUP.md`); **Project in GitHub anlegen** |
| P0-006 | Release-Gate-Regeln | Erledigt (`RELEASE_READINESS_CHECKLIST.md`) |

### Phase 1 – Bestandsaufnahme

| ID | Aufgabe | Status |
|----|---------|--------|
| P1-001 | Tests erfasst | Erledigt (`test_inventory.json`, 190 Dateien) |
| P1-002 | Testfehler gesammelt | Erledigt (`current_failures.json`, 0 offene Failures im Snapshot 2026-05-11 Nachlauf) |
| P1-003 | Legacy pi-installer/setuphelfer | Teilweise (`legacy_inventory.json`) |
| P1-004 | Services/Ports/Pfade | Teilweise (`runtime_inventory.json`) |
| P1-005 | Mount/Permission | Teilweise (`storage_permission_inventory.json`) |
| P1-006 | Build/Version | Teilweise (`version_inventory.json`) |
| P1-007 | Blocker P0–P3 | Erledigt (`blocker_inventory.json` + Blocker-Raster oben) |

### Phase 2–8 (Kurz)

| Phase | Ampel | Evidence-Anker |
|-------|-------|----------------|
| P2 Backup/Restore | Rot | `docs/evidence/backup-restore/BR-*.json` |
| P3 Hardware | Rot | `docs/evidence/hardware/HW-*.json` |
| P4 Rescue | Rot/Gelb | `docs/evidence/rescue-stick/` |
| P5 Monolith | Rot | `DOMAIN_BOUNDARIES.md`, `dangerous_couplings.json` |
| P6 Website | Gelb | `WT-*.json`, `PUBLIC_STATUS_PAGE.md` |
| P7 Affiliate | Gelb | `AT-*.json`, `docs/monetization/` |
| P8 Release | Rot | `release_readiness_gate.json` |

## Rescue Agent Stub Wave (2026-06-02)

| Bereich | Status | Hinweis |
|---|---|---|
| Fleet Heartbeat Contract | **Grün** | `status=running` neutralisiert; `agent_state`; Shell+Backend+32 pytest (2026-06-03) | `RESCUE_AGENT_CONTRACT_RESULT.md` |
| Rescue Agent Stub Wave | **Gelb** | Contract/Stub live im Repo; Deploy `/opt` drift; E2EE/nftables preview only | `RESCUE_AGENT_CONTRACT_RESULT.md` |
| Rescue Discovery | Gelb | Stub + Tests, kein Live-Netzscan |
| Rescue Pairing | Gelb | Contract/Stub, keine produktive Freigabe |
| Rescue E2EE | Gelb | Envelope-Contract/Stub, Produktivkrypto offen |
| Rescue NFTables | Gelb | Preview/Validator, `apply_allowed=false` |
| Rescue System Report | Gelb | Builder vorhanden, Safety-Facade-Lücke als review_required |
| Rescue Dashboard | Gelb | Rescue-Agent-Panel Stub integriert |
| Rescue Live Menü | Gelb | UI-Preview vorhanden, keine Live-Ausführung |

## DCC Startability Recovery (2026-06-02)

| Bereich | Status | Hinweis |
|---|---|---|
| Development Control Center Startability | Gelb | Statische Startfähigkeit belegt; Runtime-Restart/Deploy nicht ausgeführt |
| Fehlerklassifikation | Gelb | `running_profile_blocked` + `deploy_drift` |
| Runtime Gate | Gelb | Legacy non-profile-aware Hinweis, Profil-Release blockt Dev-Dashboard erwartbar |
| Backend Tests | Gelb | `partial` (pytest mit `PYTHONPATH=backend:.` für neue Module erfolgreich) |
| Rescue Agent Stub | Gelb | Commit `2e602d0`; Deploy-Sync **blockiert** (`sudo`); `/opt` ohne `rescue_agent/` | `DEPLOY_SYNC_2E602D0_POST_DEPLOY_RESULT.md` |
| **Deploy-Sync 2e602d0** | **Grün** | Deploy aus Worktree OK; `/opt` mit `app_bootstrap`+`rescue_agent`; Router-Diagnose live; Profil-Gate Exit 0 | `DEPLOY_SYNC_2E602D0_POST_DEPLOY_RESULT.md` |
| **Fleet Heartbeat Live Smoke** | **Grün** | Nach `/opt`-Script-Sync `55b7bce`: Create+Heartbeat(`running`)+Finish OK; Release-Restore ausstehend | `FLEET_HEARTBEAT_FIX_AFTER_SCRIPT_FIX_RESULT.md` |
| **Fleet Script 55b7bce in /opt** | **Grün** | `${3-}` live; Fleet-Smoke Create+HB+Finish ok | `FLEET_HEARTBEAT_FIX_AFTER_SCRIPT_FIX_RESULT.md` |
| **DCC Port Mapping** | **Grün** | 3001=UI, 8000=API, 8080=nginx (kein DCC) | `DCC_PORT_MAPPING_RESULT.md` |
| **DCC Read-Only Smoke** | **Grün** | `local_lab`: dev-dashboard 200, UI SimpleHTTP :3001 | `DCC_READONLY_SMOKE_AFTER_PORT_MAPPING.md` |
| **DCC Report Freshness** | **Grün** | Live API `recent-evidence` OK (Jun 2026 top-5, limit 5); Agent-Uploads getrennt beschriftet | `DCC_REPORT_FRESHNESS_API_LIVE_AFTER_RECOVERY.md` |
| **Backend Recovery After DCC Deploy** | **Grün** | daemon-reload gap nach Deploy; recovered; API :8000 wieder 200 | `BACKEND_RECOVERY_AFTER_DCC_DEPLOY_RESULT.md` |
| **Backend Recovery After Release Restart** | **Grün** | :8000 down nach Reload/Restart-Race; release green; DCC-Route blockiert erwartungsgemäß | `BACKEND_DOWN_AFTER_RELEASE_RESTART_RESULT.md` |
| **Developer Backend Watchdog** | **Gelb** | Live ok (/opt path, local_lab API); release restore ausstehend | `BACKEND_WATCHDOG_PATH_FIX_LIVE_INGEST_RESULT.md` |
| **Runtime Ports & Profiles Registry** | **Grün** | Live `/opt` ingest ok; `runtime_ports`+`canonical_urls` in `/api/version`; release gating+watchdog ok; QEMU nicht gelaufen | `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md` |
| **Release-Profil nach Fleet-Smoke** | **Grün** | Operator-Restore `release`; Profil-Gate Exit 0 | `RELEASE_PROFILE_RESTORE_OPERATOR_INGEST.md` |
| **Runtime-Code-Drift** | **Gelb** | Backend/Rescue/Fleet-Skript match; 4 UI/Build-Hilfsdateien differieren | `RUNTIME_DRIFT_CLASSIFICATION_AFTER_RELEASE_RESTORE.md` |
| **Rescue-Agent Ingest Stub** | **Grün** | Operator-Smoke ok (`…182452`); Register+Report+Trap release | `RESCUE_AGENT_OPERATOR_SMOKE_INGEST.md` |
| **ISO Precheck** | **Gelb** | Cleanup **ok**; Validate Exit 14 blockiert Operator-Build | `RESCUE_ISO_BUILD_TREE_CLEANUP_RESULT.md` |
| Deploy Drift | Gelb | Evidence-only HEAD; Backend/Rescue/Fleet match; 4 UI/Build-Hilfsdateien differieren | `RUNTIME_DRIFT_CLASSIFICATION_AFTER_RELEASE_RESTORE.md` |
