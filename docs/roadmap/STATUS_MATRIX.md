# Setuphelfer – Statusmatrix (Ampel)

**Stand:** 2026-05-20 — **BR-001-Pivot:** **BR-001-LIVE** experimentell/rot (kein Release-Gate, keine Live-Desktop-Gate-Retries). **BR-001-OFFLINE** (Rettungsstick) = **Release-Gate** (rot bis HW-E2E). **PKG-001**, **DEV-001**, **BR-011–BR-019** wie zuvor. **BR-004/005:** blocked an **BR-001-OFFLINE**-Archiv. Siehe `docs/architecture/BR-001_GATE_STRATEGY_DE.md`.

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
| Monolith-Audit | Rot | DOMAIN_BOUNDARIES Stub | `docs/architecture/DOMAIN_BOUNDARIES.md` |
| Website-Transparenz | Gelb | Markdown-Basis im Repo | `docs/roadmap/PUBLIC_STATUS_PAGE.md`, `docs/testing/WEBSITE_TRANSPARENCY_TEST_MATRIX.md` |
| Affiliate / Monetarisierung | Gelb | Policies als Markdown | `docs/monetization/` |
| Release Gate UG-Start | Rot | Gates nicht grün | `docs/roadmap/RELEASE_READINESS_CHECKLIST.md` |
| Development Cockpit **DEV-001** | Grün | `GET /api/dev-dashboard/*` read-only/observability grün; Rescue-ISO-Executor unter `/api/dev-dashboard/rescue-iso/*` produktiv verifiziert; kontrollierter Deploy-Helper (`/api/dev-dashboard/deploy/*`) via `systemd`-Oneshot produktiv installiert; persistente Deploy-Evidence, lokale Update-Karte und Cockpit-UI-Smoke (`?window=cockpit`) erfolgreich; USB-Write und andere verbotene Aktionen bleiben blockiert | `docs/testing/DEVELOPMENT_COCKPIT_MATRIX.md`, `docs/dev-dashboard/README.md`, `docs/dev-dashboard/DEV_CLIENT_DE.md`, `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md`, `docs/evidence/dev-dashboard/DEPLOY_HELPER_INTEGRATION_RESULT.md`, `backend/core/dev_dashboard.py`, `backend/core/deploy_manifest.py` |
| Backend-Version-Gate | Grün | Regel+Skript+`/api/version`-Diagnose im Repo; produktiver Runtime-Gate-Lauf auf `/opt/setuphelfer` liefert Exit `0` | `docs/evidence/release-gates/backend_version_update_gate.json`, `scripts/check-backend-version-gate.sh`, `docs/evidence/dev-dashboard/DEPLOY_HELPER_INTEGRATION_RESULT.md` |
| **PKG-001** Runtime-Paket-Deploy-Gate | Gelb/Rot | `.deb`-Abnahme, lokale Installation, `check-runtime-deploy-gate.sh` / `deploy_drift`; Pipeline/signiertes Repo noch nicht produktiv komplett | `docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md`, `PACKAGE_DEPLOYMENT_GATE_EN.md`, `scripts/check-runtime-deploy-gate.sh`, `scripts/runtime_deploy_gate_eval.py`, `docs/evidence/release-gates/apt_update_delivery_gap.json` |
| Cloudserver Edition | Schwarz | nach Modularisierung | — |
| **Partitions Phase 2 UI Preview Stub** | Grün | Offizieller `deploy-to-opt` (2026-05-24); Gate Exit 0; API-Smoke read-only; UI-Bundle `index-B-1eLB5j.js` aus Deploy; Browser-Checkliste `?page=partitions` | `docs/evidence/partitions/PARTITIONS_PHASE2_UI_PREVIEW_STUB.md` |
| **Rescue stick read-only build emulation** | Grün | Regression lokal grün; verbotene Live-Build-Altartefakte aus dem Build-Tree bereinigt; dokumentierte Forbidden-Tokens bleiben nur Review-/Doku-Kontext | `RESCUE_STICK_READONLY_BUILD_EMULATION.md`, `RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md` |
| **Rescue stick temp runtime bundle** | Grün | `create-temp-runtime-bundle.sh` + Validator Exit 0; MANIFEST lokal | `RESCUE_TEMP_RUNTIME_BUNDLE_RESULT.md` |
| **Rescue stick temp runtime prep** | Grün | Skripte, Runbooks, Copy-Handoff | `scripts/rescue-live/` |
| **Rescue stick Live-OS network validation** | Gelb | Session 3: Bundle ok; USB-Copy VFAT/symlinks; **kein Live-Boot** | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` |
| **Controlled ISO build prep (live-build tree)** | Grün | Tree + Bundle Validator Exit 0 | `RESCUE_CONTROLLED_ISO_BUILD_PREP_RESULT.md` |
| **Controlled ISO build execution** | Gelb | Dashboard-/Executor-Pfad fuehrt bis PHASE 4; erster produktiver `/opt`-Lauf blockiert aktuell bei `prepare_bundle`/`prepare_tree` (Temp-Bundle nicht reproduzierbar erneuert, letzter validierter Tree weiter `source_head=27d790a`); Runtime-Gate bleibt gruen, USB bleibt blockiert | `RESCUE_CONTROLLED_ISO_BUILD_RESULT.md`, `RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md`, `controlled_iso_build_latest_summary.json` |
| **Rescue ISO artifact** | Rot | Keine ISO erzeugt; erster Runtime-Lauf ueber den Dashboard-Executor vor `sudo lb build noauto` blockiert | `controlled_iso_build_latest_summary.json` |
| **Controlled ISO preparation** | Gelb | Build fehlgeschlagen; USB blocked | `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md` |
| **Rescue USB write gate** | Rot | **blocked** — `usb_write_allowed: false` | `RESCUE_USB_WRITE_GATE_RUNBOOK.md` |
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
