# Changelog

Alle wichtigen ?nderungen am PI-Installer werden hier dokumentiert.  
Details und Versionsschema: [docs/developer/VERSIONING.md](./docs/developer/VERSIONING.md).

---

## [Unreleased]

### Changed
- **App bootstrap:** `app_bootstrap` (Factory, Middleware-, Router-Registry, Startup-Diagnostik); Dev-Dashboard-Status in `core.dev_dashboard_status_service`; Safety-Facade; Boundary-Skript JSON-Modus.
- **Evidence:** `docs/evidence/monolith/*`, `app_decomposition_before_rescue_iso_gate.json`; ISO-Readiness Precheck dokumentiert (kein Build in diesem Lauf).
- **Rescue Agent / Fleet:** Contract-Stubs (`rescue_agent/`), Fleet-Heartbeat `agent_state` vs. `status=running`, DCC `RescueAgentPanel`, Live-Menü-Stub; E2EE `contract_stub_only`, nftables `apply_allowed=false`.
- **Deploy 2e602d0:** Sauberer Worktree vorbereitet; Deploy blockiert (`sudo`); Evidence unter `docs/evidence/deploy/DEPLOY_SYNC_2E602D0_*`.
- **Fleet finish Exit-1:** Triage — `fleet_session_patch` `${3:-{}}` korrumpiert JSON; Fix `${3-}`; API Finish unverändert OK.
- **Fleet smoke after script fix:** `/opt`-Script-Sync `55b7bce`; Create→Heartbeat(`running`)→Finish grün; Release-Restore Operator ausstehend.
- **DCC ports:** UI :3001, API :8000, :8080 = nginx (not SetupHelfer); docs in `DCC_PORTS_AND_URLS.md`.
- **Release restore after fleet smoke:** blocked at sudo; ingest/ISO precheck remain `blocked_by_release_restore`.
- **Operator release restore ingest:** `release` live; profile gate green; ingest stub and ISO precheck readiness unlocked (yellow, smoke not run).
- **Release restore re-ingest:** `release_restore_status=ok`, drift yellow/evidence-only, ingest primary next step.

## [1.7.3.0] — 2026-05-30

### Changed
- **Version:** Bump auf `1.7.3.0` (Development Server MVP, Rescue Agent MVP, Rescue Developer Profile, Control Center Overview).
- **Development Server:** Lokaler Lab-Telemetrie-Server runtime-validiert (`local_lab`, ingest-only).
- **Development Rescue Agent:** Read-only Collector + Dev-Server-Upload MVP.
- **Rescue Developer Profile:** Developer-Profil mit Agent-Integration und Public-Profile-Guard.
- **Control Center:** Übersicht mit Roadmap-, Telemetrie-, Doku-/Diagnostik- und Evidence-Summary (`/api/dev-dashboard/control-center-summary`).
- **Safety:** Keine Public-Telemetrie; Public Uploads und SSH bleiben disabled.

---
- Root cause: missing init=/lib/systemd/systemd in bootappend; add dbus; validator exit 15/16/17.
- Operator rebuild required; rescue stays yellow.

### Changed (Rescue ISO visual live VM operator result)
- Operator VM: bundle and DE locale OK; systemd not PID 1; backend/curl failed.
- Classification live_boot_success_systemd_init_missing; next systemd init triage.

### Changed (Rescue ISO visual live functional validation handoff)
- Test plan and artifact recheck (validator exit 0); VM test awaits VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1.
- Added visual live functional classification helper and tests.

### Changed (Rescue ISO runtime integration rebuild — operator success)
- Operator rebuild LB_EXIT=0; validate-rescue-iso-squashfs exit 0 (bundle, units, DE locale, login hints).
- Rescue stays yellow; next VM functional validation with user/live.

### Changed (Rescue ISO runtime integration rebuild — prepared)
- DE keyboard/locale/timezone in live-build includes; extended squashfs validator (exit 11–14).
- systemd enable via wants symlinks; login MOTD/issue user/live; operator rebuild required.

### Changed (Rescue ISO runtime integration — operator finding)
- Operator: no usable Setuphelfer in live VM; offline: bundle in squashfs but systemd units not enabled.
- prepare: enable units via wants symlinks, live hostname/user bootappend, squashfs validator script.

### Changed (Rescue ISO visual VM boot — operator)
- Visual QEMU: Debian 12 to login prompt (`live_system_started`); nographic serial insufficient.
- Next: live user login and Setuphelfer functional check; rescue stays yellow.

### Changed (Rescue ISO live system boot validation)
- nographic 1200s: timeout_after_bootloader (stdout identical to 600s, ISOLINUX only on serial).
- No kernel/live/setuphelfer on serial; next visual operator smoke.

### Changed (Rescue ISO VM boot timeout triage)
- Followup smoke 600s with `-nographic` shows SeaBIOS/iPXE/ISOLINUX (`bootloader_seen`); prior 120s empty stdout was QEMU mode issue, not ISO defect.
- Next `RESCUE_ISO_LIVE_SYSTEM_BOOT_VALIDATION`; rescue remains yellow.

### Changed (Rescue ISO VM boot smoke executed)
- QEMU smoke 120s without host disk: exit 124, 0 bytes serial stdout; classified `timeout_no_boot_signal`.
- Next `RESCUE_ISO_VM_BOOT_TIMEOUT_TRIAGE`; rescue remains yellow (no fake boot green).

### Changed (Rescue ISO VM boot validation prep)
- ISO rechecked (SHA256 match); QEMU 8.2.2 tooling preflight; VM boot test plan documented.
- VM smoke not executed (no VM_BOOT_SMOKE_FREIGEGEBEN); next RESCUE_ISO_VM_BOOT_SMOKE_OPERATOR_RUN.
- Rescue remains yellow; no USB/restore/hardware test.

### Fixed (Rescue ISO isohybrid � syslinux-utils must be in chroot list)
- **Root cause:** `lb_binary_iso` runs `isohybrid` in the live-build **chroot** and only auto-installs `syslinux`; `setuphelfer.list.binary` is handled by `lb_binary_package-lists` (ISO apt pool only), not the chroot.
- **Fix:** `syslinux-utils` in `setuphelfer.list.chroot`; preflight/validator/diagnostics updated accordingly.
- **Operator:** `prepare-controlled-live-build-tree.sh`, then **full** clean (chroot + cache) and rebuild � partial binary-only reset is insufficient.

### Changed (Rescue ISO chroot cleanup failure triage � RESCUE-BUILD-CHROOT-CLEANUP-001)
- **Klassifikation:** Build-Abbruch durch `chroot/proc` + fehlendes `/usr/bin/env` � nicht isohybrid.
- **Diagnostics:** Neuer Code `RESCUE-BUILD-CHROOT-CLEANUP-001` in Registry, Matcher und `classify_rescue_iso_build_attempt`.
- **Operator-Handoff:** Mount-Cleanup nur unter BUILD_TREE; kein Agent-sudo, kein Build-Retry in diesem Lauf.
- **Roadmap:** Rescue bleibt blocked; Next Prompt `RESCUE_ISO_CHROOT_MOUNT_CLEANUP_TROUBLESHOOT`.

### Changed (Operator deploy sync ingest after watchdog � runtime green)
- **Ground Truth:** Operator-Terminal: Deploy-Helper + Gate Exit **0**; Agent read-only best�tigt (health/version, deploy_drift green, `liveness.py` in `/opt`).
- **Next Prompt:** `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE` (kein Rescue in diesem Lauf).
- **Evidence:** `OPERATOR_DEPLOY_SYNC_RESULT_AFTER_WATCHDOG.md`.

### Changed (Deploy sync after watchdog � blocked in agent shell)
- **Operator-Freigabe** `DEPLOY_HELPER_SYNC_FREIGEGEBEN`: Deploy-Helper im Agent zweimal blockiert (`sudo`/`sudo -n` ? Passwort/TTY, `deploy_helper_blocked_by_sudo_tty`).
- **Gate:** vorher/nachher Exit **14**; kein Rescue; Next Prompt `DEPLOY_DRIFT_TRIAGE_AFTER_WATCHDOG`.
- **Evidence:** `DEPLOY_SYNC_AFTER_WATCHDOG_*`, Operator-Handoff.

### Changed (Backend self-healing watchdog MVP and hang isolation)
- **Liveness:** Neues Modul `backend/core/liveness.py` � `/health` und `/api/version` ohne Dashboard/Git (Git nur mit `SETUPHELFER_VERSION_INCLUDE_GIT=1`).
- **Dashboard-Isolation:** Timeouts f�r `deploy_drift`, `cockpit_enrich`; `dev_dashboard_status` in Thread mit degraded-Fallback.
- **Runtime-Gate:** Exit **18** `backend_version_endpoint_timeout` wenn `/health` OK aber `/api/version` timeoutet.
- **Watchdog-MVP (Dateien):** `scripts/healthcheck/setuphelfer-backend-healthcheck.sh`, systemd `.example`-Units, `ENABLE_RESTART=0` Default � **nicht installiert**.
- **Frontend:** `probeBackendStartup.ts` klassifiziert `backend_ok|down|hanging|degraded` vor Dashboard-Laden.
- **Evidence:** Precheck, Root-Cause-Audit, Timeout-Isolation, Watchdog-Decision, Roadmap-Delta.

### Changed (Backend startup availability and watchdog hardening baseline)
- **Backend state model:** `backend_ok`, `backend_down`, `backend_hanging`, `backend_degraded`, `backend_unknown` dokumentiert; `backend_hanging` als harter Fehler festgelegt.
- **Health/API hardening:** `/health` liefert jetzt leichtgewichtige strukturierte Minimaldaten (`status`, `service`, `version`, `timestamp`, `runtime_path`) ohne Dashboard-Scans.
- **Runtime-Gate:** Hang wird explizit erkannt (`backend_hanging_active_port_but_http_timeout`, Exit **17**) statt unspezifischem `HTTP 000000`.
- **Control Center Fail-State:** Standalone-Banner zeigt bei Timeout-Hang eine rote Backend-Fehlerkarte mit erkanntem Zustand und Operator-Next-Step statt still leerer Darstellung.
- **Tests:** Neue Tests `backend/tests/test_backend_health_startup_v1.py` und `frontend/src/components/dev-dashboard/StandaloneModeBanner.test.ts`; bestehende Loader-Tests um Timeout-Klassifikation erweitert.
- **Architektur/Runbook:** Neue Doku zu Startup-Verf�gbarkeit und Watchdog/Recovery inklusive Operator-Runbook.

### Changed (Strict mode stop of background automation and standalone visibility audit)
- **Governance stop-audit:** Neue Evidence fuer Background-Task-Stop und Git-Impact (`AUTO_BACKGROUND_TASK_STOP_AUDIT*`, `AUTO_BACKGROUND_TASK_GIT_IMPACT_AUDIT*`) mit Klassifikation `unapproved_push_detected`.
- **Runtime truth:** Read-only Availability-Audit dokumentiert `backend_hanging` (Service/Port aktiv, API-Timeout auf `/api/version`, `/health`, `/api/dev-dashboard/status`, `/api/dev-dashboard/roadmap`), ohne Restart/Deploy.
- **Standalone visibility:** Snapshot/Loader/i18n/build/test geprueft; Ursache als `backend_dependency_too_strong` dokumentiert, kein riskanter Schnellfix ohne isolierte Frontend-Ursache.
- **Regelupdate:** Verbindliche No-Background/No-Auto-Chain-Regel in `docs/developer/CURSOR_WORK_RULES.md`, Tooling-Boundary DE/EN und Dev-Dashboard-FAQ ergaenzt.

### Changed (Developer dashboard internal tooling boundary and controlled runner design)
- **Boundary:** Developer Dashboard als internes Tooling dokumentiert (`internal_tooling_only=true`, `user_facing=false`, `release_feature=false`).
- **Design:** Controlled Command Runner als allowlist-basierter Sicherheitsentwurf spezifiziert (Safety-Klassen, `argv`, getrennte stdout/stderr-Logs, Evidence-First).
- **Roadmap:** Neuer Track `developer-tooling/controlled-command-runs` auf **yellow** (25%); `TERMINAL_A_READONLY` bleibt **completed**.
- **Prompt-Entscheidung:** `DEV_DASHBOARD_CONTROLLED_COMMAND_RUNS_MVP` ist verf�gbar, aber `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE` bleibt recommended_next.
- **Nicht umgesetzt:** keine freie Shell, kein Dashboard-sudo, keine freie Command-Execution.

### Changed (Rescue ISO isohybrid binary-stage dependency)
- **Failure:** Operator build Exit **127** � `binary.sh: isohybrid: not found` after `extents written` (~452 MB); partial `chroot/binary.hybrid.iso` without hybrid step.
- **Fix:** `config/package-lists/setuphelfer.list.binary` with **`syslinux-utils`**; wrapper preflight Exit **31** (`RESCUE-BUILD-ISOHYBRID-001`); diagnostics/matcher/classification.
- **Evidence:** `rescue_iso_isohybrid_failure_latest.json`, `RESCUE_ISO_ISOHYBRID_FAILURE.md`, roadmap delta.
- **N�chster Schritt:** Operator � `prepare-controlled-live-build-tree.sh`, `./auto/clean`, Build-Retry (kein apt install im Agent-Lauf).
- **Nicht ausgef�hrt:** USB-Write, Restore, Boot-/VM-/Hardwaretest.

### Changed (Rescue ISO manual operator build � policy blocked in agent shell)
- **Wrapper:** `run-controlled-iso-build-with-logging.sh --operator-confirm-build` ? Exit **30** in Agent-Umgebung (kein TTY, kein `sudo -n`); **kein** `lb build`, **kein** ISO.
- **Evidence:** `RESCUE_ISO_MANUAL_OPERATOR_BUILD_CLASSIFICATION.md`, `controlled_iso_build_latest_summary.json`.
- **Roadmap:** Rescue bleibt **blocked**; n�chster Schritt: gleicher Prompt im **echten Operator-Terminal** nach `sudo -v` (Alternative: `RESCUE_ISO_SUDOERS_ALLOWLIST_POLICY_DESIGN`).
- **Nicht ausgef�hrt:** USB-Write, Restore, Verify Deep, Hardware-/Boot-/VM-Test.

### Changed (Deploy-helper sync verification and runtime gate green)
- **Phase-0-Gate:** Exit **0** � `/opt` synchron mit Workspace (`backend/app.py`, `dev_dashboard_manual_command_runs.py`); `deploy_drift` green, `safe_test_mode` UNLOCKED.
- **Live-API:** `GET /api/dev-dashboard/manual-command-runs` und `/roadmap` HTTP **200** unter `/opt`.
- **Deploy-Helper:** Agent konnte `setuphelfer-deploy-helper.service` nicht starten (sudo); Drift war zum Pr�fzeitpunkt bereits behoben. Evidence: `DEPLOY_HELPER_SYNC_RESULT.md`.
- **Roadmap:** `RUNTIME_DEPLOY_DRIFT_CLEANUP_AND_COCKPIT_LIVE_SYNC` **completed**; n�chster Prompt **`RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`**.

### Changed (Runtime deploy drift documentation and cockpit port clarity)
- **Phase-0-Gate:** Exit **14** (`deploy_drift_backend_files`) dokumentiert � Workspace `backend/app.py` / Command-Run-API vor `/opt`; Behebung nur per Operator Deploy-Helper (`DEPLOY_HELPER_SYNC_FREIGEGEBEN`).
- **Cockpit-Dev-URL:** Doku korrigiert � Vite `dev:cockpit` nutzt **3001** (Fallback z.?B. **3002**), nicht fest **5173** (nur `dev:tauri`).
- **Roadmap:** N�chster Prompt bei rotem Gate `RUNTIME_DEPLOY_DRIFT_CLEANUP_AND_COCKPIT_LIVE_SYNC`; Rescue-ISO-Build bleibt bis Gate Exit **0** blockiert.

### Changed (Roadmap command logging completion)
- **TERMINAL_A_READONLY** auf `completed` gesetzt; neuer gr�ner Milestone `dev-dashboard-command-logging-readonly`; System-Python-API-Tests separat **gelb** dokumentiert.
- **N�chster Prompt** bleibt `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` mit Hinweis auf Live-Deploy-Check der Cockpit-UI vor dem Build.

### Added (Dev Dashboard read-only manual command run logging)
- **Evidence:** Schema und JSON-Ablage unter `docs/evidence/dev-dashboard/manual_command_runs/` f�r vollst�ndige Operator-/Cursor-Kommandonachweise (kein Chat-only).
- **API:** `GET /api/dev-dashboard/manual-command-runs` � read-only, keine Execute-Route.
- **UI:** Panel �Manuelle Kommandol�ufe� im Developer Dashboard (Struktur).
- **Triage:** `DEV_DASHBOARD_API_TEST_SKIP_TRIAGE.md` � 11 API-Test-Skips nur bei System-`python3` ohne `fastapi`; `backend/venv/bin/python3` l�uft gr�n.

### Fixed (Dev Dashboard roadmap visibility in governance cockpit)
- **Roadmap UI:** `ExternalDevelopmentControlCenter` bindet jetzt `RoadmapDrawer` ein (vorher nur Governance-Matrix trotz API-Daten); Datenquellen-Banner und Snapshot-`areas[]` aus STATUS_MATRIX.
- **Green visibility:** `ReadyStableSection` und OK-Badges f�r belegte gr�ne Gates � ohne �nderung der Backend-Statuslogik.

### Added (Diagnostics test track and global Cursor closure rules)
- **Diagnostics / Teststrecke:** Reproduzierbare Diagnostics-Teststrecke fuer Rescue-Build-, Backup-, Restore-, Runtime-/Deploy-, Notification- und Architektur-Faelle mit Evidence-Dateien, DE/EN-Doku und gezielten Backend-Tests.
- **Diagnostics / Mapping:** Neue Diagnosecodes `RESCUE-BUILD-TOOL-001`, `RESCUE-BUILD-RSVG-001` und `NOTIFICATION-EMAIL-PROVIDER-001`; Rescue-/Provider-Limit-Fehler werden jetzt als wiederverwendbare Diagnosekandidaten dokumentiert und getestet.
- **Developer Dashboard:** `diagnostics_progress` zerlegt Diagnostics in Teilbereiche (Katalog, Matcher, API, UI, Evidence, Teststrecke sowie Rescue-/Backup-/Restore-/Runtime-/Notification-/Architecture-Teilstatus) und zeigt gelernte Fehler sowie Evidence sichtbar an.
- **Globalregeln:** Zentrale Dokumente und die Next-Prompt-Registry erzwingen jetzt fuer k�nftige Cursor-L�ufe einen ehrlichen Abschluss mit Dashboard-Fortschritt, Diagnostics-Lernfortschritt, Evidence-Verkn�pfung, Next-Prompt-Entscheidung und explizit nicht ausgef�hrten Aktionen.

### Added (Dev Dashboard roadmap and next prompt registry)
- **Development Dashboard / Roadmap:** Neue read-only Roadmap-/Meilenstein-Registry mit Bereichen, Milestones, Aufgaben, Blockern, Entscheidungen, Notizen, Evidence-Links und sichtbarer Restore-/Diagnostics-Begr�ndung.
- **Next Prompt Registry:** Pr�fbare Prompt-Registry mit Auswahlregel, `recommended_next`, Plain-Text-Export und STRICT-MODE-Template; keine Execute-Buttons und keine Runtime-Aktionen aus der Roadmap.
- **Backend / API:** Neue read-only Endpunkte unter `/api/dev-dashboard/roadmap*` f�r Bereiche, Milestones, Blocker, Entscheidungen und Prompt-Export.
- **Doku / Evidence:** Neue Audit-, Registry-, FAQ- und Knowledge-Base-Dokumente unter `docs/roadmap/`, `docs/dev-dashboard/` und `docs/evidence/roadmap/`.

### Fixed (Rescue ISO rsvg preflight and notification email provider-limit hardening)
- **Version:** Patch-Bump auf `1.7.2` in `config/version.json`, `frontend/package.json`, `frontend/src-tauri/tauri.conf.json`, `frontend/src-tauri/Cargo.toml` und Root-`package.json`.
- **Rescue ISO:** Der Dashboard-/Executor-Prebuild klassifiziert die fehlende `rsvg`-Build-Abhaengigkeit jetzt vor `lb build`, blockiert den Build mit `blocked_build_tools_missing` und zeigt nur den Operator-Hinweis `sudo apt install librsvg2-bin` an; kein automatisches `apt`, kein ISO-Build.
- **Rescue ISO / Legacy-rsvg:** `rsvg-convert` aus `librsvg2-bin` wird nicht mehr f�lschlich als komplett fehlende Host-Abh�ngigkeit behandelt. Wenn `live-build` den Legacy-Befehl `rsvg` erwartet, unterscheidet der Preflight jetzt sauber zwischen `blocked_build_tools_missing` und `blocked_legacy_rsvg_command_missing`; projektlokaler Wrapper-Support unter `build/rescue/tool-compat/bin/rsvg`, kein globaler `/usr/bin/rsvg`-Symlink.
- **Rescue ISO / Zielarchitekturen:** Dashboard-State und Evidence trennen jetzt Host-Architektur, Kandidaten (`amd64`, `i386`) und separate Deferred-Tracks (`arm64`, `armhf`). Kein Ziel wird ohne Build-/Boot-Evidence als final gr�n markiert; USB-Write bleibt blockiert.
- **Rescue ISO / erster echter amd64-Buildversuch:** Kontrollierter `lb build` f�r `amd64` wurde ausgef�hrt, aber vom vorhandenen `auto/build`-Gate mit Exit `20` bewusst gestoppt; jetzt pr�zise als `blocked_controlled_build_gate_required` statt als generischer Live-Build-Konfigurationsfehler klassifiziert, ohne USB-Write, ohne `sudo`-Fallback und ohne zweiten Build-Versuch.
- **Rescue ISO / gate-konformer Wrapper-Lauf:** Kontrollierter `amd64`-Build �ber `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build` wurde versucht, aber vor dem eigentlichen ISO-Build durch `sudo` ohne Terminal/Passwort gestoppt; sauber als `blocked_requires_operator_sudo_policy` klassifiziert, ohne unsafe Folgeaktion.
- **Rescue ISO / Operator-Policy-Gate:** Der sudo-Blocker wird jetzt als eigenes `operator_policy_gate` im Rescue-Dashboard modelliert; der Wrapper bricht ohne Root, TTY oder dokumentierte Allowlist sauber mit Exit `30` und `blocked_requires_operator_sudo_policy` ab, statt an einer Hintergrund-Passwortabfrage zu haengen. Neue Diagnosecodes: `RESCUE-BUILD-ROOT-001`, `RESCUE-BUILD-GATE-001`, `RESCUE-BUILD-ARCH-001`.
- **Notifications / E-Mail:** SMTP-Provider-Limit `554 5.7.0` wird jetzt als `notification.email.provider_limit_exceeded` behandelt, mit `email_status=failed`, `next_action=check_smtp_provider_limit_or_wait`, gelbem Email-Status und redigierter Fehlermeldung `554 5.7.0 outgoing message limit exceeded`.
- **Dashboard / i18n / Doku:** Notification-Panel, Runbooks, FAQ, KB, Evidence und Statusmatrix bilden den Provider-Limit-Fall explizit als Dashboard `green` plus Email `yellow/provider_limit` ab; kein Fake-`sent`, kein automatischer Retry.

### Added (Rescue Phase C.4 � restore preview handoff planning)
- **`rescue/restore_preview_orchestrator.py`**, **`core/restore_profiles.py`**, **`core/backup_before_write_gate.py`**: restore preview plan only (`execution_allowed: false`).
- Profile `offline-full-restore-preview`; references canonical `modules.rescue_restore_dryrun` and `modules.backup_verify`.
- Deploy route: `POST /api/deploy/rescue/restore-preview-plan`.
- Docs: `RESCUE_RESTORE_PREVIEW_HANDOFF_2026-05-20.md`, `BACKUP_BEFORE_OVERWRITE_GATE_2026-05-20.md`.
- Tests: `test_restore_profiles_offline_preview_v1`, `test_backup_before_write_gate_v1`, `test_rescue_restore_preview_plan_v1`.
- Evidence: `rescue_phase_c4_restore_preview_handoff_2026-05-20.json`.

### Added (Rescue Phase C.1�C.3 � boot context, offline-full profile, backup plan)
- **`rescue/boot_context.py`**, **`rescue/backup_orchestrator.py`**: read-only boot context and offline BR-001 backup **plan** only (`execution_allowed: false`).
- **`core/backup_profiles`**: profile `offline-full`, `get_backup_profile()`, `CANONICAL_BACKUP_RUNNER_MODULE`.
- Deploy preview routes: `POST /api/deploy/rescue/boot-context/preview`, `POST /api/deploy/rescue/offline-backup-plan`.
- Docs: `RESCUE_BOOT_CONTEXT_2026-05-20.md`, `RESCUE_OFFLINE_FULL_BACKUP_PROFILE_2026-05-20.md`, `RESCUE_OFFLINE_BACKUP_ORCHESTRATOR_2026-05-20.md`.
- Tests: `test_rescue_boot_context_v1`, `test_rescue_offline_backup_plan_v1`, `test_backup_profiles_offline_full_v1`.
- Evidence: `docs/evidence/runtime-results/rescue_phase_c_boot_context_offline_backup_2026-05-20.json`.

### Added (Core storage/mount facades � Phase B.1/B.2)
- **`core.storage_facade`**, **`core.mount_facade`**: read-only inventory/planning; Rescue deploy runners migrated.
- Docs: `MODULE_FREEZE_REGISTER_2026-05-20.md`, `CORE_STORAGE_MOUNT_FACADES_2026-05-20.md`; extended `check-module-boundaries.sh`.
- Tests: `test_core_storage_facade_v1`, `test_core_mount_facade_v1`; Evidence `core_storage_mount_facades_2026-05-20.json`.

### Added (Monolith boundary audit before rescue stick)
- Architecture audit and target boundaries: `docs/architecture/MONOLITH_BOUNDARY_AUDIT_2026-05-20.md`, `MODULE_BOUNDARIES_TARGET_2026-05-20.md`, `MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md`, `NO_DUPLICATE_MODULE_RULES.md`.
- Rescue stick core dependency map: `docs/rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md`.
- Warn-only guard: `scripts/check-module-boundaries.sh`; pytest `backend/tests/test_module_boundaries_v1.py`.
- Evidence: `docs/evidence/runtime-results/monolith_boundary_audit_before_rescue_2026-05-20.json`.

### Fixed (BR-001: Timeshift excludes, runner failure mail)
- **`full-root-stable`:** tar excludes `/timeshift` and snapshot paths (live snapshots caused `tar_failed` / `TAR_CRITICAL_WARNING` on job `6d4e161b2f8c`); `full-expert` unchanged.
- **Failure mail:** `backup_runner` uses `load_effective_notification_config()` (reads `/etc/setuphelfer/notification.env`); `setuphelfer-backup@.service` loads the same `EnvironmentFile`.

### Added (Backup pipeline: pigz, telemetry, failure mail, BR-001 stable profile)
- **Kompression:** `pigz` wenn vorhanden (`SETUPHELFER_BACKUP_COMPRESSION_ENGINE=auto|gzip|pigz`), Fallback gzip mit `compression_fallback_gzip`; explizites `pigz` ohne Binary blockiert mit `backup.compression_unavailable`.
- **Telemetrie:** Top-Level-Felder in `status.json` / API (`phase`, `written_human`, `compression_engine`, Raten, `last_error_*`, `notification_status`).
- **E-Mail:** Fehler-Mail bei `backup.failed` wenn `SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE=true`; UI-Schalter �Bei Backup-Fehler E-Mail senden�.
- **Profil `full-root-stable`:** BR-001-taugliche Excludes f�r Browser-/User-Caches (dokumentiert).
- **Development Dashboard:** Phasen, Warnungen (langer gzip-Lauf, stale progress), Fehlerbereich, BR-001-Gr�n-Regel.
- Doku: `docs/backup/BACKUP_NOTIFICATIONS_{DE,EN}.md`, `docs/backup/BACKUP_PERFORMANCE_{DE,EN}.md`, `docs/knowledge-base/backup/BR001_TAR_LIVE_CACHE_FAILURES.md`.

### Changed (Update button: manual guidance only, no GUI/apt from backend)
- **UI / `Dashboard.tsx`:** Buttons heissen nicht mehr "Update starten" / "Run update in terminal", sondern zeigen eine manuelle Anleitung (z. B. "Update-Hinweise anzeigen" / "Show update guide"). Klicks oeffnen das Sicherheits-Modal mit den Befehlen `sudo apt update` / `sudo apt upgrade` und einer **BR-001-Warnung**; kein `__TAURI__.invoke('launch_update_terminal')`-Fallback mehr.
- **API `POST /api/system/run-update-in-terminal`:** liefert immer `status=manual_required`, `code=updates.manual_terminal_required`, `commands`, `copyable_command`, `blocked_auto_execution=true`, `br001_warning` � **kein** subprocess, kein `_open_terminal_with_command`, kein `apt`.
- Hintergrund: systemd-Backend hat keine grafische Sitzung; automatisches `apt update/upgrade` ist vor BR-001 unsicher (Paketmanager-Locks).
- Tests: `backend/tests/test_update_button_manual_only_v1.py` (Endpoint ruft `subprocess.Popen` und `_open_terminal_with_command` nicht auf).
- Evidence: `docs/evidence/runtime-results/update_button_manual_only_2026-05-19.json`.

### Fixed (Web UI runtime service, production static server)
- **`setuphelfer.service`:** `scripts/start-browser-production.sh` startet die gebaute SPA mit **`exec python3 scripts/serve-frontend-production.py`** (stdlib **`ThreadingHTTPServer`**, SPA-Fallback, **`/api/*`** auf :3001 mit **404** und Hinweis auf Backend :8000). Kein **Vite preview** und kein **Node** mehr im Web-UI-Dienstprozess (weniger bewegliche Teile bei Browser-Reloads).
- Produktivstart weiterhin **ohne** `npm install` / `npm run build`; fehlendes **`frontend/dist/index.html`** beendet mit Exit **1** und klarer Meldung; **`node_modules`** ist fuer den Web-UI-Dienst nicht noetig.
- Aeltere Deployments / Diagnose: Vite im Vordergrund per `exec` (Commit **`0a1e4a0`**). Doku/KB/Evidence: `docs/operations/WEB_UI_RUNTIME_SERVICE_{DE,EN}.md`, `docs/knowledge-base/runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md`, `docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`.

### Fixed (Backend stability: system status vs. notification settings)
- **`/api/system/status`:** teure `apt`-Schritte laufen nicht mehr im Uvicorn-Event-Loop (`asyncio.to_thread`); `get_updates_categorized` verzichtet auf `apt-get update` und pro-Paket-`apt-get upgrade -s` (verhindert Minuten-Blockaden bei `workers=1` und falsche �Backend tot�-Symptomatik beim UI-Reload).
- **Benachrichtigungen:** robusteres Lesen von `notification.env` (UTF-8 mit `errors=replace`, keine Exceptions aus dem Parser), defensiver `build_public_settings`, strukturierte Fehler bei Schreibfehlern ohne Exception-Text; API-Handler mit Fallback-JSON.
- **Paketaktivitaet:** `apt-get` mit `-s` / `--simulate` / `--dry-run` gilt als nicht blockierend.
- Doku: `docs/operations/BACKUP_NOTIFICATIONS_RUNTIME_{DE,EN}.md`; Evidence: `docs/evidence/runtime-results/notification_settings_backend_crash_repair_2026-05-19.json`.

### Added (Rescue � sandbox controlled copy & build environment emulation)
- Deploy-Runner `runner_rescue_sandbox_controlled_copy.py`: Precheck, Config-/Runtime-Kopie nur unter `build/rescue/sandbox/`, SHA256-Verify, Seal, Final-Gate; Handoffs unter `docs/evidence/runtime-results/handoff/`.
- Deploy-Runner `runner_rescue_build_environment_emulation.py`: read-only Emulation (Snapshot, Workspace, Outputs-Metadaten, Logs, Overlay), Verify, Seal, Final-Gate; Artefakte unter `build/rescue/emulation/`.
- API (`/api/deploy`): `POST /rescue/sandbox-copy/{precheck,config,runtime,verify,seal,final-gate}` und `POST /rescue/build-emulation/{environment-snapshot,workspace,outputs,logs,overlay,verify,seal,final-gate}` mit passenden `DEPLOY_RESCUE_*`-Response-Codes.
- Tests: `test_deploy_runner_rescue_sandbox_controlled_copy_v1.py`, `test_deploy_runner_rescue_build_environment_emulation_v1.py`.
- Doku/KB/Evidence/i18n: u. a. `DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_{DE,EN}.md`, `DEPLOY_RESCUE_BUILD_ENVIRONMENT_EMULATION_{DE,EN}.md`, KB-Artikel und FAQ-Erg�nzungen.

### Fixed (Backup API - FIX-9 API consistency, HW pre-06)
- `GET /api/backup/list` nutzt jetzt eine eigene read-only Validierung mit `resolve_mount_source_for_path` statt der Schreibpr�fung aus Create; autofs/systemd-automount wird auf reales Blockdevice aufgel�st.
- Fehlerantworten von `backup/list` liefern strukturierte Details (`mount_source_seen`, `resolved_source`, `fstype`, `target`, `diagnosis_id`) f�r Evidence/Diagnose.
- `POST /api/backup/create` (`type=data`) gibt Source-Planung nun auch im Erfolgspfad zur�ck (`selected_sources`, `skipped_sources`, `required_sources`, `optional_sources`).
- `POST /api/backup/restore` (`mode=preview`) erg�nzt PrivateTmp-Kontext (`private_tmp_isolation`, `preview_dir_visibility_note`, `service_private_tmp_hint`).
- i18n erg�nzt: `backup.messages.preview_private_tmp_hint` (DE/EN).

### Fixed (Backup API - FIX-10 backup/list stability hardening)
- `/api/backup/list` auf read-only Pfad validiert (ohne Write-Probe), weiterhin harte Blockade f�r `/media` / `/run/media`.
- Validierung und Dateiscan in `asyncio.to_thread + asyncio.wait_for` mit kurzen harten Grenzen (3s/4s), um Worker-Blockade zu reduzieren.
- Strukturierter Timeout-Code f�r Listen-Endpunkt: `backup.list_timeout` inkl. `details.command`, `details.timeout_seconds`, `details.target`.
- Dateidatum ohne externe `date`-Subprozesse (reines `datetime.fromtimestamp`), um zus�tzliche Blockadequellen zu entfernen.
- i18n erg�nzt: `backup.messages.list_timeout` (DE/EN).

### Fixed (Backup API - FIX-11 backup/list decouple via index)
- `GET /api/backup/list` ist vom direkten Directory-Scan entkoppelt und liest prim�r aus einem lokalen Backup-Index (`backup-index.json` im State-Verzeichnis).
- Erfolgreiche Backup-L�ufe aktualisieren den Index mit Metadaten (`backup_file`, `created_at`, `encrypted`, `size_bytes`, `type`, `target`, `source_summary`, `manifest_present`, `verification_status`, `storage_path`) ohne Secrets.
- Bei fehlendem Index liefert `backup/list` deterministisch `success` mit leerer Liste und `index_available=false` statt Mount-Scan.
- Optionale Existenzpr�fung pro Indexeintrag ist kurz getaktet (`quick_stat`); bei Timeout bleibt der Eintrag sichtbar mit `status=unknown`.
- `/media` und `/run/media` bleiben sofort blockiert (`backup.path_invalid`, `STORAGE-PROTECTION-005`) ohne Dateisystemscan.

### Fixed (Backup API - FIX-12 restore enforcement)
- `POST /api/backup/restore` trennt `mode=preview` und `mode=restore` jetzt strikt; `mode=restore` l�uft nicht mehr durch den Preview-Pfad.
- API-Vertrag gesch�rft: bei `mode=restore` ist `target_dir` Pflicht (`backup.restore_target_missing`), `target_dir="/"` wird hart blockiert.
- Restore-Ziele werden bei `mode=restore` deterministisch validiert; ung�ltige Ziele liefern `backup.restore_target_invalid`, nicht beschreibbare Ziele `backup.restore_not_writable`.
- Erfolgs-Code f�r echten Restore erg�nzt: `backup.restore_success`; Preview bleibt `backup.restore_preview_ok`.

### Fixed (Storage Protection - FIX-8 runtime path verification)
- Ursache fuer weiterhin auftretendes `STORAGE-PROTECTION-004` im aktiven Backup-Pfad nachgewiesen: Runtime unter `/opt/setuphelfer` war teils nicht synchron und der Backup-Target-Validator nutzte einen abweichenden Mount-Pfad.
- `core.safe_device.resolve_mount_source_for_path()` erweitert: `str|Path`, rekursive `findmnt -R`-Flattening, automount-Trigger-Retry, und lsblk-Fallback wenn `PrivateDevices=yes` den direkten `/dev/*`-stat verhindert.
- `modules.storage_detection.validate_backup_target()` auf dieselbe robuste Mount-Aufloesung umgestellt (`resolve_mount_source_for_path`) statt separater, uneinheitlicher `findmnt`-Entscheidung.
- Neue Tests: `test_storage_detection_fix8_runtime_v1.py` plus erweiterte `test_safe_device_storage_protection_v1.py` (nested automount/retry).

### Fixed (Storage Protection - FIX-7 automount source resolution)
- `backend/core/safe_device.py`: robuste Mount-Source-Aufloesung fuer `validate_write_target()` via `findmnt -J -T` inkl. Layer-Fall `systemd-1/autofs` -> reales Blockgeraet.
- UUID-Sources (`/dev/disk/by-uuid/...`) werden auf das echte Blockdevice aufgeloest und als Blockgeraet verifiziert; bei Unsicherheit bleibt `STORAGE-PROTECTION-004` bestehen.
- Fehlerdetail bei `STORAGE-PROTECTION-004` erweitert (u. a. `mount_source_seen`, `resolved_source`, `fstype`, `target`, `reason`) fuer bessere Evidence.
- Tests erweitert: autofs/systemd-automount, UUID-Source, unknown/unsafe Source bleibt blockiert.

### Added (Service conflict guard, pi-installer vs. Setuphelfer)
- Neues Modul `backend/core/service_conflict_guard.py`: systemd-/Pfad-/Port-8000-Erkennung, keine blinde Prozessbeendigung ueber die API.
- `GET /api/system/service-conflicts` (nur lesend); Preflight in `scripts/start-backend.sh` und vor `uvicorn.run` in `app.py` (`__main__`).
- Diagnosekatalog `SERVICE-CONFLICT-033` bis `036` plus Matcher-Signale; Tests `backend/tests/test_service_conflict_guard_v1.py`.
- `debian/postinst` und `scripts/install-system.sh`: klar geloggt stop/disable von `pi-installer*.service`, Downgrade-Schutz fuer `/opt/setuphelfer` (optional `SETUPHELFER_ALLOW_DOWNGRADE=1`).
- Doku: `docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md`, `docs/developer/NAMING_AND_SERVICES.md`, `docs/faq/SERVICE_CONFLICT_FAQ.md`.

### Fixed (Backup API � FIX-2 sudo gate, HW1 / NoNewPrivileges)
- **`POST /api/backup/create`:** kein pauschales `sudo -n true` mehr fuer **`type=data`** und **`target=local`** nach erfolgreicher Zielvalidierung (`_validate_backup_dir` / Allowlist); Zielverzeichnis per **`os.makedirs`** ohne sudo. Bei fehlenden Rechten: **`backup.mkdir_failed`** mit **`PERM-GROUP-008`**. Wenn sudo weiterhin noetig ist (z. B. Full-Backup) und NNP sudo blockiert: neuer API-Code **`backup.sudo_blocked_by_nnp`** mit Detail **`SYSTEMD-NNP-031`**. Tests: `backend/tests/test_backup_create_sudo_gate_v1.py`.

### Fixed (Backup API - FIX-3 data source scope, HW1)
- `type=data` nutzt einen nicht-privilegierten Quell-Scope ohne pauschales `/opt`; root-/container-nahe Pfade (z. B. `/opt/containerd`) sind nicht mehr Teil des Data-Backups.
- Nicht lesbare optionale Quellen werden als `skipped_sources` dokumentiert; nicht lesbare Pflichtquellen liefern strukturiert **`backup.source_permission_denied`** mit Details (`unreadable_sources`, `required_permission`) und `diagnosis_id=BACKUP-SOURCE-PERM-032`.
- Tar-`Permission denied` im Data-Pfad wird auf denselben strukturierten API-Code gemappt statt nur als Rohfehltext.
- Tests erg�nzt: `backend/tests/test_backup_data_source_scope_v1.py`.

### Fixed (Backup Runtime - FIX-4 source trace + path unification, HW1)
- Runtime-Mismatch behoben: aktiver `type=data`-Pfad nutzt nicht mehr die Altliste `/home /var/www /opt`, sondern ausschlie�lich Source-Planning.
- Harte Ausschlussregel f�r Data-Backups erg�nzt: gesamter `/opt`-Tree (inkl. `/opt/containerd`) wird in `type=data` nie als `selected_sources` akzeptiert.
- Strukturierte Trace-Logs vor Tar-Lauf erg�nzt (`backup_type`, `target`, `selected_sources`, `skipped_sources`, `required_sources`, `optional_sources`, `effective_tar_command`).
- Fehlerdetails bei `backup.source_permission_denied` erweitert um `selected_sources`, `skipped_sources`, `required_sources`, `optional_sources` (weiterhin `diagnosis_id=BACKUP-SOURCE-PERM-032`).
- Eingebetteter Scheduler-Runner (`_render_backup_runner_script`) auf dieselbe Data-Source-Planung umgestellt, damit API- und Runtime-/Scheduler-Pfad konsistent sind.

### Fixed (Backup API - FIX-5 data home model, HW1)
- `type=data` verwendet als Pflichtquelle ausschlie�lich das Home des **effektiven Dienstnutzers** (`pwd.getpwuid(os.geteuid()).pw_dir`) statt implizitem Login-Shell-Kontext.
- Home-Readchecks behandeln `PermissionError` nun deterministisch als lesbarkeitsbezogenen Source-Fehler; dadurch wird der strukturierte Pfad `backup.source_permission_denied` (`BACKUP-SOURCE-PERM-032`) statt ungemapptem `backup.error` genutzt.
- Keine automatische Aufnahme fremder Home-Verzeichnisse unter `/home/*`; Data-Backup bleibt strikt service-context-basiert ohne sudo.

### Added (Backup API - FIX-6 data test source model, HW1)
- F�r reproduzierbare HW-L�ufe unterst�tzt `type=data` jetzt explizite Pflichtquellen �ber `SETUPHELFER_DATA_BACKUP_SOURCES` (z. B. `/mnt/setuphelfer/test-data`).
- Ist die Variable gesetzt, ersetzt sie die Default-Pflichtquelle (Service-Home) vollst�ndig; `/home` ist dann keine implizite Voraussetzung f�r HW-Success.
- Konfigurierte Quellen werden nur unter `/mnt/setuphelfer` akzeptiert (Allowlist), `/opt/*` bleibt weiterhin hart ausgeschlossen.

### Added (Diagnose-Assistent, Phase DIAG-1 Kern)
- Neuer strukturierter Diagnosekern unter `backend/core/diagnostics/` mit stabilem Katalog (30 Faelle), deterministischem Matcher und API-Endpunkten `POST /api/diagnostics/analyze`, `GET /api/diagnostics/catalog`, `GET /api/diagnostics/{id}`.
- Frontend-Erweiterung: `DiagnosticsAssistantPanel` mit Ausgabe nach Nutzerstufe (Beginner/Advanced/Expert), angebunden im Backup/Verify-Flow.
- Wissensbasis erweitert um `docs/knowledge-base/diagnostics/*` (Architektur, Datenmodell, Katalog, Matching-Regeln, UI-Stufen).

### Added (Diagnose-Lernschleife, Phase DIAG-1.1)
- Strukturiertes Evidenz- und Hardwareprofil-Modell (`EvidenceRecord`, `SystemProfile`, `StorageDevice`) inkl. API-Endpunkte `GET /api/diagnostics/evidence/schema` und `GET /api/diagnostics/evidence/sample`.
- Persistente Evidenz-/Profilablage unter `data/diagnostics/evidence/` und `data/diagnostics/profiles/` mit Seed-Faellen aus bekannten Projektproblemen.
- Diagnosekatalog-Rueckkopplung um Evidence-Zaehler und Kontexte (`seen_in_platforms`, `common_*_contexts`) erweitert.
- Neue Pflichtdokumentation fuer Lernschleife und Entwicklerworkflow (`EVIDENCE_MODEL.md`, `LEARNING_LOOP.md`, `TEST_SCENARIO_CATALOG.md`, `HARDWARE_PROFILE_SCHEMA.md`, `DIAGNOSTIC_DEVELOPMENT_WORKFLOW.md`).

### Added (HW-TEST-1 Vorbereitung vor Pi-Isolationstest)
- Strikte Hardware-Testmatrix mit 24 Szenarien fuer Linux-Laptop -> externe NVMe, USB-3.2-Stick (64 GB), SD-Karte (64 GB) inkl. Negativ-/Grenzfaelle in `data/diagnostics/hw_test_1_matrix.json`.
- Neue Test-Evidence-Dokumente fuer Matrix, Durchfuehrung und Pi-Freigabegate unter `docs/knowledge-base/test-evidence/`.
- Zusaetzliche System-/Medienprofile fuer Laptop und Wechselmedien unter `data/diagnostics/profiles/`.
- Geplantes Evidence-Template fuer noch nicht ausgefuehrte Realhardwarelaeufe sowie optionaler Dev-Helper `scripts/diagnostics/new_evidence_record.py`.
- Neue Konsistenztests fuer HW-Matrix und Profile (`backend/tests/test_hw_test_1_matrix_v1.py`, `backend/tests/test_hw_profiles_v1.py`).

### Added (HW-EXEC-1 externe NVMe, reale Evidenz)
- Reale Ausfuehrung von `HW1-01` bis `HW1-05` mit jeweils genau einem EvidenceRecord (`EVID-2026-HW1-01` bis `EVID-2026-HW1-05`), inklusive fehlgeschlagener und inkonklusiver Ergebnisse.
- Neuer Ausfuehrungsreport `docs/knowledge-base/test-evidence/HW_EXEC_1_EXTERNAL_NVME_REPORT.md` mit Diagnose-/Ursachenbewertung pro Test.
- Diagnosekatalog erweitert um `SYSTEMD-NNP-031` (NoNewPrivileges blockiert sudo im Restore-/Runtime-Pfad).

### Fixed (Backup / Recovery - Symlinks und Sonderdateien, file-based)
- Symbolische Links werden als Symlinks archiviert (ohne Dereferenzierung); rekursive Sammlung mit `os.walk(..., followlinks=False)`.
- Sockets/FIFOs/Geraete: nicht archiviert, Eintrag unter `skipped_members` statt komplettem Abbruch.
- `backend/modules/backup_symlink_safety.py`: Pruefung relativer Symlink-Ziele gegen Pfadflucht aus Restore-/Verify-Wurzel.
- Verify/Restore: symbolische Tar-Mitglieder erlaubt; `extractall` bevorzugt `filter="tar"`; Manifest `type` / `link_target`; kein `Path.resolve()` auf Symlink-Leafs in der Verifikation.

### Fixed (Backup / Recovery � file-based engine hardening)
- `backend/modules/backup_engine.py`: file-based Backup archiviert jetzt Dateien **und** Verzeichnisse rekursiv mit relativen, kollisionsgesch�tzten Archivpfaden; �berlappende Eingaben werden dedupliziert und im Manifest dokumentiert (`skipped_inputs`).
- `backend/modules/backup_verify.py`: Verify blockiert unsichere Archiv-Member (Traversal, absolute Pfade, Link-/Sondertypen) und pr�ft Manifestpfade konsistent zur extrahierten Struktur.
- `backend/modules/restore_engine.py`: Restore entpackt nur sichere Member, blockiert Traversal/Link-/Sondertypen und schreibt `MANIFEST.json` nicht in das Restore-Ziel.
- `backend/tests/test_backup_recovery_engines.py`: Tests f�r rekursive Verzeichnisarchivierung, relative Pfade, Kollisionsfehler, Restore-Pfadstruktur, Manifest/Archiv-Inkonsistenz und Allowlist-Schutz erweitert.
- Dokumentation aktualisiert: `docs/developer/BACKUP_RECOVERY_ENGINES.md`, `docs/faq-source-notes.md`, `docs/knowledge-base/BACKUP_RECOVERY_FILE_ENGINE_REALITY.md`, `docs/knowledge-base/README.md`.

### Added (Dokumentation / Wissensbasis)
- Neue Host-Umgebungsdoku unter `docs/host-env/` (`README`, `FAQ`, Wissensdatenbank, Docker-Desktop/MCP-Hinweise, Chat-Zusammenfassung) zur reproduzierbaren lokalen Arbeitsumgebung.
- Wissensbasis erweitert um `docs/knowledge-base/APT_REPOSITORIEN_UND_DOCKER_FAQ.md` und `docs/knowledge-base/CHAT_ZUSAMMENFASSUNG_APT_DOCKER_2026-04.md`.

### Notes
- Die File-Engine-H�rtung verbessert die technische Wiederherstellbarkeit, ersetzt aber keinen echten Full-Recovery-Nachweis mit VM-Reboot und anschlie�endem Hardware-Test.


---

## [1.5.0.0] - 2026-04-22

### Added

- Deterministischer Restore-Pfad ohne manuelle API-Workarounds; verpflichtendes **Manifest** im Archiv (Fail-Fast bei fehlendem oder ung�ltigem `MANIFEST.json`).
- Zweisprachige Backend-Texte f�r `backup_recovery_i18n` �ber Locale (`SETUPHELFER_LANG` / `LC_MESSAGES` / `LANG` mit Pr�fix `de`) sowie erg�nzte Frontend-Keys (`backup.messages.*`, `verify.messages.*`, `restore.messages.*`).
- Wissensbasis: [docs/knowledge-base/FULL_RESTORE_BOOT_TEST.md](docs/knowledge-base/FULL_RESTORE_BOOT_TEST.md) mit DE/EN-Kurzfassung und Verweis auf den VM-Report.

### Changed

- **systemd**-Units und Installer-Flow stabilisiert (Speicherlimits, Capabilities, Finalpr�fung aktiver Dienste nach `install-system.sh`).
- Dokumentation zu Backup-/Recovery-Engines und Manifest um deterministisches Verhalten und englische Kurzabschnitte erg�nzt.

### Fixed

- Restore-/Boot-Themenkreis in Doku und FAQ konsolidiert; fehlende i18n-Zuordnung f�r u. a. `backup.failed_manifest_missing` / Archiv-Integrit�t in der Web-UI.

---

## [1.4.1.0] - 2026-04-07

### Added (Backup / Recovery � Engines & Doku)
- **Backend:** `backup_engine`, `backup_verify`, `restore_engine`, `backup_crypto` (AES-256-GCM), `recovery_transport`; Hilfen `block_device_allowlist`, `backup_path_allowlist`, `backup_recovery_i18n`.
- **CLI:** `recovery/main.py` (Recovery-Men� bei unvollst�ndigem Root).
- **Tests:** `backend/tests/test_backup_recovery_engines.py` (Simulation Zerst�rung/Wiederherstellung in `/tmp`).
- **Doku:** `docs/developer/BACKUP_RECOVERY_ENGINES.md`; In-App **Backup & Restore** + **FAQ**; i18n-Keys `documentation.backupRestore.*`, `documentation.faq.backupEngines.*`.
- **Hinweis:** Schl�ssel f�r Verschl�sselung werden **nicht** ins Backup geschrieben; Boot-Tests auf echter Hardware weiterhin manuell.

---

## [1.4.0.5] - 2026-04-07

### Changed (Betrieb � Setuphelfer-Standard, PI_INSTALLER Legacy)
- **`scripts/deploy-to-opt.sh`:** `mkdir -p` f�r **`STATE_DIR`** vor `chown`; Texte/Titel Setuphelfer; Hinweis zu Unit-Platzhaltern `{{PI_INSTALLER_*}}`.
- **`scripts/install-system.sh`:** Banner/Fehlertexte Setuphelfer; **`SETUPHELFER_USE_SERVICE_USER`** / **`SETUPHELFER_USER`** mit Fallback auf `PI_INSTALLER_*`; **`chown`/`chmod`** f�r **`STATE_DIR`**; Symlink **`setuphelfer` ? `start-setuphelfer.sh`**; **`profile.d`:** Prim�r `SETUPHELFER_*`, `PI_INSTALLER_*` nur als Spiegel aus denselben Werten.
- **`backend/core/install_paths.py`:** `_env_path_setup_then_legacy` � explizit SETUPHELFER vor PI_INSTALLER (Bugfix: `get_state_dir` nutzte f�lschlich `_env_path_first`).
- **`scripts/install-backend-service.sh`**, **`create_installer.sh`:** `SETUPHELFER_*`-Variablen zuerst; **`sudo mkdir -p`** f�r Config/Log/State vor Service-Install.
- **`scripts/start-setuphelfer.sh`:** **`SETUPHELFER_MODE`** vor **`PI_INSTALLER_MODE`**.
- **`scripts/uninstall-system.sh`:** Kopfkommentar Setuphelfer.
- **`docs/architecture/NAMING_AND_SERVICES.md`:** ENV-Reihenfolge pr�zisiert.

---

## [1.4.0.4] - 2026-04-07

### Added (Phase F � Zielsystem-Pr�fung)
- **`scripts/verify-setuphelfer-install.sh`** � Pr�ft **systemd** (`setuphelfer-backend` / `setuphelfer`, Legacy `pi-installer*`), **curl** auf `/api/version` und Web-UI :3001, optional **journalctl**; Exit-Code 0/1.
- **`docs/VERIFY_TARGET_SYSTEM.md`** � Kurzanleitung und manuelle Kommandos; Verweise in `NAMING_AND_SERVICES.md`, `architecture/README.md`, `SYSTEM_INSTALLATION.md`.

---

## [1.4.0.3] - 2026-04-07

### Changed (Phase D4 � Changelog-, Versions- und FAQ-Pflege)
- **Workflow:** `.cursor/rules/projekt-workflow.mdc` � einheitliche Quelle **`config/version.json`**, Sync per `sync-version.js`; Changelog-Pflicht; systemd **setuphelfer-backend** in Abschnitt 6.
- **Doku:** `docs/developer/VERSIONING.md` � Titel Setuphelfer, Abschnitt **�Release-Pflicht f�r Maintainer (Phase D4)�** (Checkliste: version.json, sync, CHANGELOG.md, In-App-Changelog, FAQ, debian/changelog).
- **In-App:** FAQ-Eintrag **�Version und Changelog � wo wird was gepflegt?�** f�r Mitwirkende; Versionsblock **1.4.0.3**.

---

## [1.4.0.2] - 2026-04-07

### Changed (Architektur & Review � Phase D3)
- **Referenz:** `docs/architecture/NAMING_AND_SERVICES.md` � Produktname, Debian-Source vs. Binary-Paket `setuphelfer`, Pfade, systemd-Units, ENV (`SETUPHELFER_*` / `PI_INSTALLER_*`), Tauri-Binary-Hinweis.
- **Index:** `docs/architecture/README.md` � Einstieg in Architektur-Dokumente.
- **Aktualisiert:** `init_flow.md`, `config_flow.md`; Review: `phase1_structure.md`, `phase4_structural_simplification.md`, `repository_consistency_report.md`, `error_backlog_current_state.md` (A-02 eingegrenzt).

---

## [1.4.0.1] - 2026-04-07

### Changed (Dokumentation � Phase D2)
- **Nutzerdoku:** `docs/START_APPS.md`, `docs/BETRIEB_REPO_VS_SERVICE.md`, `docs/SYSTEM_INSTALLATION.md`, `docs/SD_CARD_IMAGE.md` auf **Setuphelfer**-Pfade und **systemd**-Units (`setuphelfer.service`, `setuphelfer-backend.service`) ausgerichtet; Legacy-Hinweise f�r `pi-installer` &lt; 1.4.0 wo n�tig.
- **In-App:** `Documentation.tsx` � FAQ (Starter, Pfade), Versionsblock **1.4.0.1**; **README** � Kurzverweis auf `/opt/setuphelfer`.
- **Skripte:** `install-system.sh` � Zusammenfassung nach Installation (Befehle, systemd, Startmen�); `uninstall-system.sh` � Entfernen der Symlinks **`setuphelfer*`**, Desktop-Dateien **`setuphelfer*.desktop`**, optionaler User **`setuphelfer`**.

---

## [1.4.0.0] - 2026-04-08

### Changed (Breaking � Betrieb)
- **Produkt-/Service-Name:** Debian-Binarypaket **`setuphelfer`** (ersetzt `pi-installer` &lt; 1.4.0); System-User **`setuphelfer`**; Pfade **`/opt/setuphelfer`**, **`/etc/setuphelfer`**, **`/var/lib/setuphelfer`**, **`/var/log/setuphelfer`**.
- **systemd:** **`setuphelfer-backend.service`** + **`setuphelfer.service`**; Vorlagen im Repo-Root `setuphelfer*.service`; alte `pi-installer*.service` werden bei Deploy/postinst stillgelegt.
- **Backend:** zentrale Pfadlogik `backend/core/install_paths.py`; **`_config_path()`** ohne Home-Fallback im Service-Modus; **`PI_INSTALLER_CONFIG_DIR`** / **`SETUPHELFER_*`** wirksam; Backup/Audit/Support-Bundle auf dynamische Pfade.

---

## [1.3.9.5] - 2026-04-07

### Fixed
- **Service-Topologie:** Port **8000** geh�rt nur noch **`pi-installer-backend.service`**. `scripts/start-browser-production.sh` startet kein Uvicorn mehr; bei fehlendem API klare Fehlermeldung und Exit.
- **systemd:** `pi-installer.service` **`Requires=pi-installer-backend.service`** (DEB + Vorlagen); **`debian/pi-installer-backend.service`** im Paket; `postinst`/`prerm`/`deploy-to-opt.sh`/`install-system.sh`/`create_installer.sh` aktivieren/starten Backend vor Web-UI.
- **APP_EDITION:** Explizit **`release`** in Unit-Vorlagen (zus�tzlich zu DEB); Pfade **`PI_INSTALLER_*`** per Platzhalter in beiden Vorlagen.
- **install-backend-service.sh:** Unter **`/opt/pi-installer`** User **`pi-installer`**, falls vorhanden.

### Changed
- **Doku:** `docs/BETRIEB_REPO_VS_SERVICE.md`; **uninstall-system.sh:** beide Units entfernen.

---

## [1.3.9.4] - 2026-04-07

### Fixed
- **Betrieb / systemd:** `pi-installer.service` startet nicht mehr `./start.sh` (Vite-Dev, Schreibzugriffe auf `frontend/node_modules/.vite`). Stattdessen `scripts/start-browser-production.sh` mit `vite preview` auf gebautem `frontend/dist/` und optionalem Vite-Cache unter `/tmp` (`PI_INSTALLER_VITE_CACHE_DIR`).
- **Deploy:** `scripts/deploy-to-opt.sh` f�hrt `npm run build` aus und schreibt die gleiche `ExecStart`-Zeile.

### Changed
- **Dokumentation:** `docs/BETRIEB_REPO_VS_SERVICE.md` (Repo-Modus vs. Service-Modus); Verweise in `docs/START_APPS.md`, `docs/SYSTEM_INSTALLATION.md`; FAQ und Versionskapitel in der App.

---

## [1.3.9.3] - 2026-04-07

### Changed
- **Backup & Restore:** Ampel auf **Freigabelage Phase 3** ausgerichtet (kein Gr�n ohne nachgewiesenen Backup-Lauf; Gelb bei �Kern nicht verifiziert�; Rot bei `sudo_required` bzw. Diagnose/Restore-Vorschau-Risiko); Pflicht-Hinweistext per i18n.
- **Dokumentation:** `docs/developer/BACKUP_RESTORE_PHASE3_RELEASE_ASSESSMENT.md` erg�nzt/verwendet; Verifikationsnotiz Phase 2D/2E referenziert.

### Notes
- Keine neue Backup-Kernfunktion; keine Produktionsfreigabe behauptet.

---

## [1.3.9.2] - 2026-04-03

### Added
- **Diagnose (Architektur):** Kanonisches �bergangsschema `localization_model` (`legacy` \| `key_v1`), i18n-Key-Felder (`title_key`, `user_message_key`, `suggested_action_keys`), `diagnosis_code`, Referenzen (`docs_refs`, ?) in `backend/models/diagnosis.py`; Doku `docs/architecture/diagnosis_localization.md`.
- **Backend-Interpreter:** `interpret_v1` auf **v2**; Webserver-Portkonflikt, Backup-Verify-Fehler, System-Backend-unreachable und generischer Fallback liefern **key_v1** + EN-Fallback-Strings; Firewall-Regeln vorerst **legacy** (deutsche Freitexte, `schema_version` 1).

### Changed
- **Frontend:** `DiagnosisPanel` w�hlt Texte per Keys oder Legacy; Typen in `types/diagnosis.ts`; `localBackendDiagnosis` / `localDiagnosisFallback` auf **key_v1**; neue Keys unter `diagnosis.codes.*` in `de.json` / `en.json`.
- **Version:** Patch `1.3.9.2` (`config/version.json`).

---

## [1.3.9.1] - 2026-04-03

### Added
- **Entwicklungsprozess:** Verbindliche Regeln f?r Cursor/Modulbearbeitung in `docs/developer/CURSOR_WORK_RULES.md` (Vorpr?fung, keine blinden Installationen, Testnachweise, Modulvollst?ndigkeit, i18n-Pflicht, Doku/FAQ/Changelog/Version-Matrix, Standard-Bericht).
- **Checklisten:** `docs/developer/MODULE_EDIT_CHECKLIST.md`, Berichtsvorlage `docs/developer/CHANGE_REPORT_TEMPLATE.md`, Index `docs/developer/README.md`.
- **Verweise:** `CONTRIBUTING.md` und `docs/architecture/ARCHITECTURE.md` verlinken die neuen Vorgaben.

### Changed
- **Version:** Patch auf `1.3.9.1` (kanonisch `config/version.json`).

---

## [1.3.9.0] - 2026-04-03

### Added
- **Gef?hrte Nutzung (Frontend):** Zentrales Modul- und Bereichsmodell (`frontend/src/beginner/moduleModel.ts`), wiederverwendbare Marker f?r ?Gesperrt / Sp?ter / Fortgeschritten? (`BeginnerGuidanceMarker`).
- **Dashboard (Einsteiger):** Hervorgehobener Block ?N?chster sinnvoller Schritt?, empfohlene Aktionen, getrennte Bereiche f?r optional und sp?tere Module.
- **App Store (Einsteiger):** Empfohlene Apps zuerst, Hinweis-Badges und sortierte Darstellung.
- **Backup (Einsteiger):** Drei klare Einstiege (erstellen, pr?fen, wiederherstellen); erweiterte Tabs unter ?Weitere Optionen?.
- **Dokumentation:** `docs/user/GUIDED_UX_AND_COMPANION.md`; Handbuchtexte und **FAQ** in der App (Erfahrungslevel, Panda-Begleiter, Einsteigerf?hrung); Eintrag im Kapitel **Einstellungen** (Erfahrungslevel).
- **Desktop:** `SetupHelfer.desktop` mit Logo-Icon; Starter `scripts/start-pi-installer.sh` mit Auswahl **Tauri / Browser / Nur Backend**; Debian- und Install-Skripte angepasst.
- **Profil-API:** Schreib-Fallback f?r `user_profile.json` unter `~/.config/pi-installer/`, wenn `/etc/pi-installer/` nicht beschreibbar ist; Frontend wertet FastAPI-`detail` bei Fehlern aus.

### Changed
- **Version:** Kanonisch `1.3.9.0` in `config/version.json`; `sync-version.js` synchronisiert auch die Root-`package.json`.
- **Navigation (Einsteiger):** Optional Badge ?Fortgeschritten? bei Monitoring in der Sidebar.

---

## [1.3.8.4] - 2026-04-03

### Changed
- Versionsnummer auf 1.3.8.4 angehoben (kanonisch `config/version.json`).

---

## [1.3.8.1] - 2026-03-12

### Added
- **Sicherheit:** CORS auf konfigurierbare Origins beschr?nkt (Standard: localhost; LAN ?ber `PI_INSTALLER_CORS_ORIGINS`).
- **Sicherheit:** Sudo-Passwort nur noch verschl?sselt (Fernet) im Speicher, TTL 30 Min; Key in Installationsverzeichnis oder `~/.config/pi-installer/`.
- **Sicherheit:** Rate-Limiting auf `/api/users/sudo-password` (10/Min); Security-Header (X-Content-Type-Options, X-Frame-Options, Referrer-Policy).
- **Sicherheit:** Systemd-Services geh?rtet (ProtectSystem=strict, PrivateTmp, NoNewPrivileges, MemoryMax, LimitNOFILE).
- **Doku:** SECURITY.md (Netzwerk LAN/Internet, VPN-Empfehlung, Firewall); docs/user/NETWORK_ACCESS.md.
- **Version:** Einzige Quelle `config/version.json`; sync-version.js schreibt auch VERSION, package.json, Tauri.

### Changed
- Versionsnummer auf 1.3.8.1 angehoben (Patch: Security & Repo-Optimierungen).

---

## [1.3.8.0] - 2026-03-06

### Added
- **Remote Companion (Phase 1) ? Dokumentation:** ?bersicht und Architektur in `docs/REMOTE_COMPANION.md` (API, Rollen, Events, Datenmodell, Phase-2-Ausblick). Entwicklerleitfaden in `docs/REMOTE_COMPANION_DEV.md` (Modul registrieren, Widgets, Aktionen, Eventbus). Verweise in README und In-App-Dokumentation.
- Phase-2-Vorbereitung konzeptionell beschrieben: Sync-Status, Ordner-Profile, CalDAV/CardDAV-Healthcheck als sp?tere Integrationspunkte (ohne Implementierung).

### Changed
- Versionsnummer auf 1.3.8.0 angehoben (neues Feature: Remote-Companion-Dokumentation).

---

## [1.3.7.6] - 2026-03-05

### Fixed
- OLED-Erkennung im Control Center auf `i2cdetect -r` umgestellt, damit keine falschen OLED-Treffer auf ungeeigneten I2C-Bussen mehr gemeldet werden.
- Hardware-Diagnose erg?nzt: Wenn `dtparam=i2c_arm=on` fehlt und `/dev/i2c-1` nicht existiert, wird klarer, warum der Runner kein OLED erreichen kann.

---

## [1.3.7.5] - 2026-03-05

### Fixed
- OLED-Telemetrie-Endpunkte im Backend wiederhergestellt (`/api/control-center/display/telemetry` und Runner-Action-Endpunkt), damit die OLED-Anzeige im Control Center wieder korrekt geladen und gesteuert werden kann.
- OLED-Autostart beim Backend-Start wieder aktiviert, sodass die Anzeige nach einem Neustart automatisch anlaufen kann.
- OLED-I2C-Erkennung auf variable Busse erweitert (`/dev/i2c-*` statt hart nur Bus 1), damit die Anzeige auch auf Systemen mit anderen I2C-Busnummern wieder gefunden wird.

---

## [1.3.7.4] - 2026-03-05

### Added
- Skript **backup-sd-card.sh**: Sicherheits-Backup der SD-Karte (Boot + Root), optional Ziel NVMe (`--nvme`) mit ext4 f?r vollst?ndiges Backup
- Doku **NVME_BOOT_FREENOVE_SWITCH.md**: Boot von NVMe hinter Freenove-PCIe-Switch, EEPROM, UART-Debug, SD-Backup-Hinweise
- Verweise auf NVMe-Boot-Freenove in NVME_FULL_BOOT.md und PATHS_NVME.md

### Changed
- backup-sd-card.sh: Unterst?tzung f?r Zielfs ext4 (volle rsync-Optionen) bzw. vfat (eingeschr?nkt)
- Sync mit GitHub: Stand origin/main (1.3.4.15) integriert, lokale ?nderungen (Backup, NVMe-Docs) beibehalten

---

## [1.3.4.15] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.15

### Changed
- Build-Prozess optimiert


## [1.3.4.14] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.14

### Changed
- Build-Prozess optimiert


## [1.3.4.13] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.13

### Changed
- Build-Prozess optimiert


## [1.3.4.12] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.12

### Changed
- Build-Prozess optimiert


## [1.3.4.11] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.11

### Changed
- Build-Prozess optimiert


## [1.3.4.10] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.10

### Changed
- Build-Prozess optimiert


## [1.3.4.9] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.9

### Changed
- Build-Prozess optimiert


## [1.3.4.8] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.8

### Changed
- Build-Prozess optimiert


## [1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.7

### Changed
- Build-Prozess optimiert


## [1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.6

### Changed
- Build-Prozess optimiert


## [1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version 1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:51:30][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:51:30][0m Aktuelle Version: 1.3.4.8
[0;32m[2026-02-16 16:51:30] ?[0m Version erh?ht: 1.3.4.8 -> 1.3.4.9
[0;32m[2026-02-16 16:51:30] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:51:30] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.9] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:51:30][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:51:30][0m Aktuelle Version: 1.3.4.8
[0;32m[2026-02-16 16:51:30] ?[0m Version erh?ht: 1.3.4.8 -> 1.3.4.9
[0;32m[2026-02-16 16:51:30] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:51:30] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.9

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:47:56][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:47:56][0m Aktuelle Version: 1.3.4.7
[0;32m[2026-02-16 16:47:56] ?[0m Version erh?ht: 1.3.4.7 -> 1.3.4.8
[0;32m[2026-02-16 16:47:56] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:56] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.8] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:47:56][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:47:56][0m Aktuelle Version: 1.3.4.7
[0;32m[2026-02-16 16:47:56] ?[0m Version erh?ht: 1.3.4.7 -> 1.3.4.8
[0;32m[2026-02-16 16:47:56] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:56] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.8

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:47:14][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:47:14][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:47:14] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:47:14] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:14] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:47:14][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:47:14][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:47:14] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:47:14] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:47:14] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:46:47][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:46:47][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:46:47] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:46:47] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:46:47] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:46:47][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:46:47][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:46:47] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:46:47] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:46:47] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:44:28][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:44:28][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:44:28] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:44:28] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:44:28] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:44:28][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:44:28][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:44:28] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:44:28] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:44:28] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:41:24][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:41:24][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:41:24] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:41:24] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:41:24] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:41:24][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:41:24][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:41:24] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:41:24] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:41:24] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:39:06][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:39:06][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:39:06] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:39:06] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:39:06] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:39:06][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:39:06][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:39:06] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:39:06] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:39:06] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:38:32][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:38:32][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:38:32] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:38:32] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:38:32] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.7
1.3.4.7] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:38:32][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:38:32][0m Aktuelle Version: 1.3.4.6
[0;32m[2026-02-16 16:38:32] ?[0m Version erh?ht: 1.3.4.6 -> 1.3.4.7
[0;32m[2026-02-16 16:38:32] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:38:32] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.7
1.3.4.7

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:35:29][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:35:29][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:35:29] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:35:29] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:35:29] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:35:29][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:35:29][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:35:29] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:35:29] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:35:29] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
1.3.4.6

### Changed
- Build-Prozess optimiert


## [[0;36m[2026-02-16 16:32:16][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:32:16][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:32:16] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:32:16] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:32:16] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.6
1.3.4.6] - 2026-02-16

### Added
- Automatisches Release: Version [0;36m[2026-02-16 16:32:16][0m Schritt 1: Version erh?hen...
[0;36m[2026-02-16 16:32:16][0m Aktuelle Version: 1.3.4.5
[0;32m[2026-02-16 16:32:16] ?[0m Version erh?ht: 1.3.4.5 -> 1.3.4.6
[0;32m[2026-02-16 16:32:16] ?[0m Tauri-Version aktualisiert: 1.3.4
[0;32m[2026-02-16 16:32:16] ?[0m Cargo.toml-Version aktualisiert: 1.3.4
[sync-version] version -> 1.3.4.6
1.3.4.6

### Changed
- Build-Prozess optimiert


## [1.3.4.2] ? 2026-02

### DSI Radio (v2.1.0) ? NDR-Ton, Backend, Doku

- **NDR 1 / NDR 2 ? Ton funktioniert:** Die App bevorzugt jetzt getestete Stream-URLs aus `stations.py` (icecast.ndr.de). Wenn NDR 1 oder NDR 2 aus der Sendersuche stammen, werden die oft fehlerhaften addradio.de-URLs durch die funktionierenden icecast-URLs ersetzt. Siehe FAQ: ?NDR 1 / NDR 2: Kein Ton?.
- **Audio-Ausgabe auf dem Laptop:** Der explizite Pulse-Sink wird nur noch auf dem Freenove-Ger?t gesetzt. Auf dem Linux-Rechner nutzt GStreamer das System-Standard-Ausgabeger?t ? kein erzwungener Sink mehr, Ton l?uft ?ber das gew?hlte Ger?t.
- **Backend-Start (PEP 668):** `start-backend.sh` und `start.sh` verwenden durchg?ngig die Venv im Backend-Verzeichnis (`venv/bin/python3`, `venv/bin/pip`). Kein ?externally-managed-environment?-Fehler mehr bei System-Python 3.12+.
- **DSI Radio ? Anweisungen:** Fehlermeldungen und README nennen jetzt ?im Terminal auf dem Linux-Rechner?, Beispielpfad `/home/volker/piinstaller`, Aufruf mit `sudo bash ?` bei ?Befehl nicht gefunden?. Backend-Hinweis f?r Logos/Sendersuche erg?nzt.
- **FAQ:** Neuer Eintrag ?NDR 1 / NDR 2: Kein Ton? (Stream-URL-Preferenz aus stations.py).

### Dokumentation

- **apps/dsi_radio/README.md:** Linux-Terminal-Anweisungen, Backend f?r Logos/Sendersuche, ?Befehl nicht gefunden? mit `sudo bash` und Zeilenumbr?che.
- **docs/START_APPS.md:** Backend manuell im Terminal starten (z. B. Laptop); DSI-Radio-Bedarf am Backend erw?hnt.

---

## [1.3.4.1] ? 2026-02

### Radio-App (DSI Radio) ? Metadaten-Verbesserungen

- **System-Metadaten aus PulseAudio/PipeWire:** Die App liest jetzt Titel/Interpret direkt aus dem Lautst?rkeregler-System (PulseAudio/PipeWire) ? dieselbe Quelle wie der System-OSD. Fallback wenn Backend/GStreamer keine Metadaten liefern.
- **"Es l?uft:" immer sichtbar:** Die Zeile "Es l?uft:" bleibt immer sichtbar, auch wenn kein Sendungsname vorliegt (zeigt dann nur "Es l?uft:" ohne Text dahinter).
- **Logo und Sendername beim Wiederherstellen:** Beim App-Start wird der zuletzt angeh?rte Sender korrekt wiederhergestellt ? Logo und Sendername werden sofort aktualisiert.
- **Show-Metadaten-Erkennung:** Sendungsnamen wie "Die Show" oder "1LIVE Liebesalarm" werden automatisch als Show-Metadaten erkannt und erscheinen hinter "Es l?uft:", nicht mehr als Titel/Interpret.
- **Interpret-Textgr??e:** Interpret-Label hat jetzt die gleiche Schriftgr??e wie der Titel (14 statt 13), bleibt aber nicht fett dargestellt.

---

## [1.3.4.0] ? 2026-02

### Systemweite Installation gem?? Linux FHS

- **Neue Installationsmethode:** Systemweite Installation nach `/opt/pi-installer/` gem?? Linux Filesystem Hierarchy Standard (FHS)
- **Installations-Skripte:**
  - `scripts/install-system.sh` ? Systemweite Installation nach `/opt/pi-installer/`
  - `scripts/update-system.sh` ? Update-Skript f?r bestehende Installationen
  - `scripts/install.sh` ? Wrapper mit interaktiver Auswahl zwischen beiden Methoden
- **Installationsverzeichnisse:**
  - Programm: `/opt/pi-installer/`
  - Konfiguration: `/etc/pi-installer/`
  - Logs: `/var/log/pi-installer/`
  - Symlinks: `/usr/local/bin/` (globale Befehle wie `pi-installer`, `pi-installer-backend`)
- **Umgebungsvariablen:** Automatisch in `/etc/profile.d/pi-installer.sh` gesetzt
- **systemd Service:** Verbesserte Sicherheitseinstellungen (NoNewPrivileges, PrivateTmp, ProtectSystem)
- **Dokumentation:** Neue Dokumentation `docs/SYSTEM_INSTALLATION.md` mit vollst?ndiger Anleitung
- **GitHub-Integration:** Alle Installations-Skripte direkt von GitHub verf?gbar ?ber Raw-URLs

### Dual Display X11 ? Fr?he Konfiguration

- **LightDM Integration:** Verwendet `session-setup-script` f?r fr?he Display-Konfiguration nach Login
- **Position korrekt:** DSI-1 wird zuerst gesetzt (links unten 0x1440), dann HDMI-1-2 (rechts oben 480x0)
- **Keine mehrfachen Umschaltungen:** Atomare Konfiguration in einem xrandr-Befehl
- **Alte Skripte deaktiviert:** Automatische Deaktivierung von `enable-hdmi.sh` und verz?gerten Autostart-Skripten
- **Skript:** `scripts/fix-gabriel-dual-display-x11-early.sh` f?r optimierte fr?he Konfiguration

---

## [1.3.3.0] ? 2026-02

### Dual Display X11 ? stabil ohne st?ndiges Umschalten

- **Stand:** DSI + HDMI unter X11 l?uft jetzt richtig; Position (DSI links unten, HDMI rechts oben), Desktop/Hintergrund auf HDMI (Primary), keine st?ndige Umschaltung mehr.
- **Ma?nahmen:** Atomarer xrandr-Befehl (beide Ausgaben in einem Aufruf); .xprofile setzt Layout nach 8 s und startet ~10 s nach Login PCManFM-Desktop neu (Trigger: Desktop ? Primary/HDMI); delayed-Script wendet Layout nach 8 s und 16 s an; optional `fix-desktop-on-hdmi-x11.sh` zum manuellen Neustart des Desktops.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) ? Spiegelung, Position, Desktop auf HDMI, Trigger, Beschleunigung (~10 s), FAQ-Verweise.
- **FAQ:** Eintrag ?Dual Display X11 (DSI + HDMI) ? Desktop auf HDMI, stabil? erg?nzt; bestehender Eintrag zur DSI-Spiegelung beibehalten.

---

## [1.3.2.0] ? 2026-02

### Dual Display X11 ? DSI-Spiegelung auf HDMI

- **Problem:** Der komplette DSI-1-Desktop wurde oben links auf HDMI-1-2 gespiegelt (nicht nur ein Fenster). Ursache: Pi-KMS/DRM-Treiber legt die HDMI-Scanout-Region nicht korrekt ab Offset (480,0).
- **Ma?nahmen in Scripts:** Explizite Framebuffer-Gr??e `xrandr --fb 3920x2240`; Konfiguration **HDMI vor DSI** (HDMI 480x0, dann DSI 0x1440). Angepasst: `fix-gabriel-dual-display-x11.sh`, `.xprofile`, `.screenlayout`, `apply-dual-display-x11-delayed.sh`, `fix-dsi-position-x11.sh`.
- **Dokumentation:** [docs/DSI_HDMI_SPIEGELUNG_X11.md](docs/DSI_HDMI_SPIEGELUNG_X11.md) ? Problem, umgesetzte Ma?nahmen, optionale config.txt-Workarounds, manuelle Tests.
- **FAQ:** Neuer Eintrag ?DSI-Desktop oben links auf HDMI gespiegelt (X11)? in der App-Dokumentation (Dokumentation ? FAQ) und Verweis in docs/VIDEO_TUTORIALS.md.

---

## [1.3.1.0] ? 2026-02

### Backup & Restore ? Laufwerk klonen & NVMe

- **Laufwerk klonen:** Neue Funktion in Backup & Restore ? System von SD-Karte auf NVMe/USB-SSD klonen (Hybrid-Boot: Kernel von SD, Root von NVMe). rsync-basiert, fstab und cmdline.txt werden automatisch angepasst.
- **NVMe-Erkennung:** Ziel-Laufwerke (NVMe, USB, SATA) werden ?ber disk-info API erkannt und im Clone-Tab angezeigt. Modell, Gr??e und Mount-Status sichtbar.
- **Festgestellte Probleme:** Siehe Dokumentation ? FAQ f?r bekannte Einschr?nkungen und L?sungswege (z.?B. NVMe-Pfade nach Clone, Dualdisplay-Konfiguration, Freenove-Case-Anpassungen).

### DSI-Radio (Freenove TFT ? native PyQt6-App)

- **Lautst?rke:** Regler steuert den aktiven Kanal (PulseAudio: `pactl set-sink-volume @DEFAULT_SINK@`; Fallback: ALSA amixer Master/PCM). Regler rechts neben Senderbuttons, oberhalb des Seitenumschalters (1/2 ?), silber umrandet.
- **Radioanzeige:** Logo links (96?96), rechts schwarzer Klavierlack-Rahmen mit leuchtend gr?ner Anzeige und schwarzer Schrift; Schlie?en-Button (?) in der Anzeige; Uhr mit Datum, kompakt.
- **D/A-Umschalter:** Langgestrecktes rotes O mit rundem schwarzem Schieber, D (Digital/LED) und A (Analog); analoge VU-Anzeige mit Skala 0?100 %, rechts roter Bereich, Zeiger begrenzt durch Lautst?rke.

### Dokumentation

- **Neue Bereiche:** ?Freenove Pro ? 4,3? Touchscreen im Geh?use? und ?Dualdisplay DSI0 + HDMI1 ? Zwei Monitore gleichzeitig? mit Tips & Tricks.
- **Lernbereich:** Themenblock ?Touchscreen am DSI0 Port? erg?nzt.
- **FAQ:** Aus Troubleshooting eine vollst?ndige FAQ mit Fehlername, Beschreibung und L?sungen; funktionales Design mit logischer Farbgebung; FAQ-Eintrag ?DSI-Radio: Lautst?rke funktioniert nicht? erg?nzt.

---

## [1.3.0.1] ? 2026-02

### Backup & Restore

- **Cloud-Backups l?schen:** L?schung von Cloud-Backups (WebDAV/Seafile) funktioniert; URL-Konstruktion aus PROPFIND-`href` korrigiert (`base_domain + href`); Debug-Info in Response f?r Fehlerf?lle.
- **USB ? Cloud Wechsel:** Beim Wechsel von USB zu Cloud und zur?ck werden die Backups des zuvor gemounteten USB-Sticks wieder geladen; `loadBackups(dirOverride)` und explizites Setzen von `backupDir` + Aufruf beim USB-Button.
- **Kein Cloud-Upload bei USB-Ziel:** Backups mit Ziel USB-Stick werden nicht mehr zus?tzlich in die Cloud hochgeladen; Backend l?dt nur noch bei `target` `cloud_only` oder `local_and_cloud`, nicht bei `local`.

---

## [1.3.0.0] ? 2026-02

### Transformationsplan: ?Raspberry Discovery Box?

- **App Store:** Neue Seite mit 7 Apps (Home Assistant, Nextcloud, Pi-hole, Jellyfin, WordPress, VS Code Server, Node-RED); Kachel-Layout, Suche, Kategorien; Ein-Klick-Installation (API vorbereitet, Implementierung folgt).
- **First-Run-Wizard:** Beim ersten Start: Willkommen ? Optional (Netzwerk/Sicherheit/Backup) ? ?Was m?chtest du tun?? (Smart Home, Cloud, Medien, Entwickeln) ? Empfohlene Apps ? App Store.
- **Dashboard-Redesign:** Hero ?Dein Raspberry Pi l?uft!?, gro?er Status (Alles OK / Aktion ben?tigt), Ressourcen-Ampel (CPU/RAM/Speicher), Schnellaktionen (Neue App installieren, Backup erstellen, System updaten).
- **Mobile:** Hamburger-Men? auf kleinen Screens; Sidebar als Overlay; touch-freundlich; responsive Padding.
- **Kontextsensitive Hilfe:** HelpTooltip-Komponente (?-Icon) an Dashboard und App Store.
- **Einstellungen:** Option ?Erfahrene Einstellungen anzeigen? (versteckt; blendet Grundlegende Einstellungen und Dokumentations-Screenshots ein).
- **Fehlerfreundliche Texte:** App-Store-Installation: ?Huch, das hat nicht geklappt ?? statt technischer Fehlermeldung.
- **Installer & Docs:** Single-Script-Installer (`create_installer.sh`), systemd-Service (`pi-installer.service`), One-Click-Dokumentation (get.pi-installer.io); Python 3.9+ in Doku und requirements.

---

## [1.2.0.6] ? 2026-02

### NAS: Duplikat-Finder (Phase 1)

- **Duplikate & Aufr?umen:** Neuer Bereich in der NAS-Seite ? fdupes/jdupes installieren, Verzeichnis scannen, Duplikate in Backup verschieben (statt l?schen).
- **Installation:** Fallback auf jdupes, wenn fdupes nicht verf?gbar; klarere Fehlermeldungen von apt.
- **Scan:** Vorgeschlagener Pfad (Heimatverzeichnis, wenn /mnt/nas nicht existiert); Option ?System-/Cache-Verzeichnisse ausschlie?en? (.cache, mesa_shader, __pycache__, node_modules, .git, Trash) ? Standard: an.
- **API:** `POST /api/nas/duplicates/install`, `POST /api/nas/duplicates/scan`, `POST /api/nas/duplicates/move-to-backup`.
- **Dokumentation:** INSTALL.md ? Troubleshooting Duplikat-Finder-Installation; NAS-Dokumentation um Duplikate-Bereich erg?nzt.

---

## [1.2.0.5] ? 2026-02

### Dokumentation

- **Raspberry Pi 5: Kein Ton ?ber HDMI** ? Troubleshooting erweitert: typische Symptome (amixer ?cannot find card 0?, /dev/snd/ nur seq/timer, PipeWire nur Dummy Output), Ursache (fehlender Overlay vc4-kms-v3d-pi5), konkrete Schritte. In App-Dokumentation (Troubleshooting), INSTALL.md und PI_OPTIMIZATION.md erg?nzt.

---

## [1.2.0.4] ? 2026-02

### Pi-Optimierung & Erkennung

- **Pi-Erkennung:** Fallback ?ber Device-Tree (`/proc/device-tree/model`) ? Raspberry Pi wird auch erkannt, wenn vcgencmd/cpuinfo fehlschlagen.
- **Raspberry Pi Config:** Men?punkt erscheint nun zuverl?ssig, sobald ein Pi erkannt wird.
- **CPU-Auslastung reduziert:** Light-Modus f?r Polling (`/api/system-info?light=1`); Dashboard-Polling auf dem Pi alle 30 s; Monitoring ohne Live-Polling auf dem Pi; Auslastung nur noch im Dashboard, nicht in Submen?s.
- **UI:** Card-Hover ohne Bewegung (nur Farbwechsel); StatCard-Icon ohne Animation; Hardware & Sensoren: Stats-Merge beh?lt Sensoren/Laufwerke beim Polling.

### Dokumentation

- `PI_OPTIMIZATION.md`: Hinweise zu Pi-Erkennung, Raspberry Pi Config und abschaltbaren Services.

---

## [1.2.0.3] ? 2026-02

### Mixer-Installation

- **Backend:** Update und Install in zwei Schritten (`apt-get update`, dann `apt-get install`); Dpkg-Optionen `--force-confdef`/`--force-confold` f?r nicht-interaktive Installation; bei Fehler wird `copyable_command` zur?ckgegeben; Timeout-Meldung klarer.
- **Frontend (Musikbox & Kino/Streaming):** Bei Fehler erscheint unter den Mixer-Buttons ein Hinweis ?Installation fehlgeschlagen. Manuell im Terminal ausf?hren:? mit Befehl und **Kopieren**-Button.

---

## [1.2.0.2] ? 2026-02

### Ge?ndert

- **Dashboard ? Hardware & Sensoren:** Bereich ?Systeminformationen? entfernt (ist bereits in der ?bersicht sichtbar).
- **CPU & Grafik:** Treiber-Hinweise (NVIDIA/AMD/Intel) werden nicht mehr unter der CPU angezeigt, sondern unter der jeweiligen Grafikkarte (iGPU bzw. diskret).

### Dokumentation

- In der Anzeige (Dokumentation ? Versionen & Changelog) nur die Endversion mit Details; ?ltere Updates kompakt bzw. ?berspringbar.

---

## [1.2.0.1] ? 2026-02

### Behoben

- **Dashboard ? IP-Adressen:** Text unter den IPs (?Mit dieser IP von anderen Ger?ten erreichbar??) war anthrazit und bei Hover unleserlich ? jetzt `text-slate-200` und Link `text-sky-200`.
- **Dashboard ? Updates:** Zeile ?X Notwendig ? Y Optional? war zu blass ? jetzt `text-slate-200` / `text-slate-100` f?r bessere Lesbarkeit.
- **Dashboard ? Men?:** Buttons ??bersicht?, ?Auslastung & Grafik?, ?Hardware & Sensoren? ? inaktive Buttons hatten fast gleiche Farbe wie Schrift ? jetzt `text-slate-200`, `bg-slate-700/70`, Hover `bg-slate-600`.
- **CPU & Grafik:** Es wurden 32 ?Prozessoren? (Threads) gelistet ? ersetzt durch **eine** CPU-Zusammenfassung: Name, Kerne, Threads, Cache (L1?L3), Befehlss?tze (aufklappbar), Chipsatz/Mainboard; integrierte Grafik und Grafikkarte unver?ndert; Auslastung nur noch physikalische Kerne (keine Thread-Liste).
- **Mixer-Installation:** Installation schlug weiterhin fehl ? Sudo-Passwort wird getrimmt; `apt-get update -qq` vor install; `DEBIAN_FRONTEND=noninteractive` f?r update und install; Timeout 180s; Fehlermeldung bis 600 Zeichen; Logging bei Fehler.

### Backend

- `get_cpu_summary()`: Liest aus /proc/cpuinfo und lscpu Name, Kerne, Threads, Cache (L1?L3), Befehlss?tze (flags).
- System-Info liefert `cpu_summary`; `hardware.cpus` wird auf einen Eintrag reduziert (keine Liste aller Threads).

---

## [1.2.0.0] ? 2026-02

### Neu

- **Musikbox fertig:** Musikbox-Bereich abgeschlossen ? Mixer-Buttons (pavucontrol/qpwgraph), Installation der Mixer-Programme per Knopfdruck (pavucontrol & qpwgraph), Sudo-Modal f?r Mixer-Installation.
- **Mixer:** Mixer in Musikbox und Kino/Streaming eingebaut ? ?Mixer ?ffnen (pavucontrol)? / ?Mixer ?ffnen (qpwgraph)? starten die GUI-Mixer; ?Mixer-Programme installieren? installiert pavucontrol und qpwgraph per apt; Backend setzt `DISPLAY=:0` f?r GUI-Start; Installation mit `DEBIAN_FRONTEND=noninteractive` f?r robuste apt-Installation.
- **Dashboard:** Erweiterungen und Quick-Links; Versionsnummer und Changelog auf 1.2.0.0 aktualisiert.

### API

- `POST /api/system/run-mixer` ? Grafischen Mixer starten (Body: `{"app": "pavucontrol"}` oder `{"app": "qpwgraph"}`).
- `POST /api/system/install-mixer-packages` ? pavucontrol und qpwgraph installieren (Body optional: `{"sudo_password": "..."}`).

### Dokumentation

- Changelog 1.2.0.0 in App (Dokumentation ? Versionen & Changelog).
- Troubleshooting: Mixer-Installation fehlgeschlagen (manueller Befehl, Sudo, DISPLAY) in Dokumentation und INSTALL.md.
- INSTALL.md: API Mixer (run-mixer, install-mixer-packages); FEATURES.md: v1.2 Features; README Version 1.2.0.0.

---

## [1.0.4.0] ? 2026-01

- Sicherheit-Anzeige im Dashboard (2/5 aktiviert bei Firewall + Fail2Ban).
- Dokumentation & Changelog aktualisiert.

---

?ltere Eintr?ge siehe **Dokumentation** in der App (Versionen & Changelog).
