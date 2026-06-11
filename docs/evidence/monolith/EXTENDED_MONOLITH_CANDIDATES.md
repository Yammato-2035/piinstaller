# Extended Monolith Candidates

**Datum:** 2026-06-10  
**HEAD:** `9005c54`

## Legende

- **Risiko:** LOW / MEDIUM / HIGH / CRITICAL  
- **Priorität:** P1 Sofort / P2 Kurzfristig / P3 Mittelfristig / P4 Später

---

## Kritische Backend-Monolithen

| Datei/Modul | Zeilen | Hauptdomäne | Nebendomänen | Verantwortlichkeiten | Risiko | Priorität |
|-------------|--------|-------------|--------------|----------------------|--------|-----------|
| `backend/app.py` | 17.857 | Runtime | Backup, Security, Users, NAS, Web, Mail, Monitoring, Partitions, Settings, i18n-API | FastAPI-App, ~213 Routen, Middleware, Logging, Systeminfo, sudo, Backup-API, User-API, Hardware | **CRITICAL** | **P1** |
| `backend/deploy/routes.py` | 5.003 | Deployment | Rescue, DCC, Governance, Verify | ~227 Deploy-Runner-Routen, Orchestrierung, Evidence | **CRITICAL** | **P1** |
| `backend/modules/control_center.py` | 1.990 | Companion Dashboard | Monitoring, Device Discovery | Steuerzentrale, Status-Aggregation | **HIGH** | **P2** |
| `backend/tools/backup_runner.py` | 1.583 | Backup | Verify, Diagnostics | CLI-Backup, Tar, Manifest, Evidence | **HIGH** | **P2** |
| `backend/core/rescue_fat32_esp_usb_writer.py` | 1.469 | Rescue Stick | Storage, Safety, Deploy | USB-Schreiben, FAT32, ESP, Hardstops | **CRITICAL** | **P1** |
| `backend/core/dev_dashboard.py` | 1.217 | Development Control Center | Deployment, Diagnostics, Governance | DCC-Status, Module, Evidence-Index | **HIGH** | **P2** |
| `backend/core/rescue_iso_build_state.py` | 1.021 | Rescue | Deployment, Diagnostics | ISO-Build-State-Machine | **HIGH** | **P2** |
| `backend/core/safe_device.py` | 993 | Storage | Backup, Safety | Geräte-Sicherheit, Write-Guard | **HIGH** | **P2** |
| `backend/modules/raspberry_pi_config.py` | 969 | Provisioning | Hardware, Security | config.txt, GPIO, Overlays | **MEDIUM** | **P3** |
| `backend/core/dev_dashboard_roadmap.py` | 773 | Development Control Center | Dokumentation | Roadmap, Prompts, Export | **MEDIUM** | **P3** |
| `backend/core/dev_dashboard_cockpit.py` | 731 | Development Control Center | Deployment | Cockpit-Aggregation | **MEDIUM** | **P3** |
| `backend/modules/backup_engine.py` | 677 | Backup | Restore, Verify | Backup-Orchestrierung | **HIGH** | **P2** |
| `backend/modules/backup.py` | 592 | Backup | Security | Backup-Contract, API-Helfer | **MEDIUM** | **P3** |
| `backend/core/notification_service.py` | 593 | Benachrichtigungssystem | Telemetrie, DCC | E-Mail, Events, State | **MEDIUM** | **P3** |
| `backend/core/fleet_session_state.py` | 658 | Development Server | Rescue, Telemetrie | Fleet-Sessions | **MEDIUM** | **P3** |
| `backend/core/storage_role_classification.py` | 472 | Partitionshelfer / Storage | Device Discovery | Rollenklassifikation | **MEDIUM** | **P4** (stabil) |
| `backend/api/routes/partitions.py` | ~200 | Partitionshelfer | Storage, Safety | Extrahiert — Vorbild | LOW | P4 |

---

## Kritische Frontend-Monolithen

| Datei/Modul | Zeilen | Hauptdomäne | Nebendomänen | Verantwortlichkeiten | Risiko | Priorität |
|-------------|--------|-------------|--------------|----------------------|--------|-----------|
| `frontend/src/pages/BackupRestore.tsx` | 3.992 | Backup | Restore, Verify, Storage | UI + Wizard + API + State + Manifest | **CRITICAL** | **P1** |
| `frontend/src/pages/ControlCenter.tsx` | 2.681 | Companion Dashboard | Monitoring, Device Discovery | Karten, Status, Navigation | **HIGH** | **P2** |
| `frontend/src/pages/InspectRun.tsx` | 2.385 | Diagnostics | Rescue, Verify | Inspect-Runs, Evidence | **HIGH** | **P2** |
| `frontend/src/pages/Dashboard.tsx` | 2.291 | Companion Dashboard | i18n, Onboarding | Startseite, Kacheln, Backend-Status | **HIGH** | **P2** |
| `frontend/src/pages/Documentation.tsx` | 2.055 | Dokumentation | i18n | Hilfe, FAQ-Einbettung | **MEDIUM** | **P3** |
| `frontend/src/pages/SettingsPage.tsx` | 1.716 | Runtime | Security, i18n | Einstellungen, API-Base, Experience | **HIGH** | **P2** |
| `frontend/src/pages/ExternalDevelopmentControlCenter.tsx` | 856 | Development Control Center | Deployment | Standalone DCC-Fenster | **HIGH** | **P2** |
| `frontend/src/pages/DevDashboardBody.tsx` | 626 | Development Control Center | Deployment, Rescue | DCC-Hauptlayout | **HIGH** | **P2** |
| `frontend/src/App.tsx` | 732 | Runtime | Alle Pages | Routing, Shell, Modals, Theme | **HIGH** | **P2** |
| `frontend/src/components/dev-dashboard/RescueBuildPanel.tsx` | 673 | Rescue | Deployment | ISO-Build-UI | **MEDIUM** | **P3** |
| `frontend/src/components/RunningBackupModal.tsx` | 472 | Backup | Monitoring | Laufendes Backup-Overlay | **MEDIUM** | **P3** |
| `frontend/src/components/PartitionWizardModal.tsx` | 356 | Partitionshelfer | — | Legacy-Wizard (Phase 2 read-only) | **MEDIUM** | **P4** |
| `frontend/src/pages/PartitionManager.tsx` | ~270 | Partitionshelfer | Storage | Workbench (neu modularisiert) | LOW | P4 |

---

## Architektur-Monolithen (Cluster)

| Struktur | Umfang | Hauptdomäne | Risiko | Priorität |
|----------|--------|-------------|--------|-----------|
| `backend/deploy/runner_*.py` | 115 Dateien, ~37k Zeilen | Deployment | **CRITICAL** | **P1** — Registry C.1 (**nicht refaktoriert**) |
| `backend/core/dev_dashboard_*.py` | 8+ Dateien | Development Control Center | **HIGH** | **P2** |
| `backend/core/notification_*.py` | 4 Dateien | Benachrichtigungssystem | **MEDIUM** | **P3** |
| `backend/core/rescue_*.py` | 25+ Dateien | Rescue | **HIGH** | **P2** |
| `frontend/src/components/dev-dashboard/*` | ~20 Dateien, ~4k+ Zeilen | Development Control Center | **HIGH** | **P2** |
| `frontend/src/locales/{de,en}.json` | je 3.379 Zeilen | i18n (alle Domänen) | **HIGH** | **P3** |

---

## Daten-Monolithen

| Datei | Zeilen/Größe | Domäne | Risiko | Priorität |
|-------|--------------|--------|--------|-----------|
| `frontend/src/locales/de.json` | 3.379 | i18n | HIGH | P3 |
| `frontend/src/locales/en.json` | 3.379 | i18n | HIGH | P3 |
| `docs/evidence/` (gesamt) | 794 MD, ~36k Zeilen | Testing / Governance | MEDIUM | P4 |
| `build/rescue/.trash/*/MANIFEST.json` | ~14k Zeilen je Datei | Rescue | MEDIUM | P4 (Aufräumen) |
| `docs/faq/BACKUP_RESTORE_FAQ_*.md` | ~1.470 je | Backup + Restore | MEDIUM | P3 |

---

## Betriebs-Monolithen

| Datei | Zeilen | Domäne | Risiko | Priorität |
|-------|--------|--------|--------|-----------|
| `scripts/rescue-live/prepare-controlled-live-build-tree.sh` | 1.059 | Rescue Build | HIGH | P2 |
| `scripts/release-service.sh` | 847 | Deployment | HIGH | P2 |
| `scripts/deploy-to-opt.sh` | 325 | Deployment | HIGH | P2 |
| `scripts/audit-setuphelfer-installations.sh` | 436 | Verify / Diagnostics | MEDIUM | P3 |

---

## Wissens-Monolithen

| Datei | Zeilen | Themen | Risiko | Priorität |
|-------|--------|--------|--------|-----------|
| `docs/faq/BACKUP_RESTORE_FAQ_DE.md` | 1.477 | Backup, Restore, FAQ, Safety | MEDIUM | P3 |
| `docs/developer/WORKFLOW_LAPTOP_PI.md` | 644 | Deploy, Rescue, Hardware | MEDIUM | P4 |
| `docs/architecture/ARCHITECTURE.md` | 400 | Gesamtarchitektur (veraltet?) | MEDIUM | P3 |

---

## Top 10 Refactoring-Kandidaten (priorisiert)

| Rang | Modul | Zeilen | Warum |
|------|-------|--------|-------|
| 1 | `backend/app.py` | 17.857 | Zentraler API-Monolith, höchstes Fan-In, blockiert Testbarkeit |
| 2 | `backend/deploy/routes.py` | 5.003 | Zweiter API-Monolith, Deploy+Rescue vermischt |
| 3 | `frontend/src/pages/BackupRestore.tsx` | 3.992 | Größte UI-Monolith-Komponente |
| 4 | `backend/deploy/runner_*` Cluster | ~37k | 115 Runner — **C.1 Registry** (`runner_registry.py`); Facade/Risk Gate C.3/C.4 offen |
| 5 | `frontend/src/pages/ControlCenter.tsx` | 2.681 | Companion-Dashboard ohne Modulgrenzen |
| 6 | `backend/core/rescue_fat32_esp_usb_writer.py` | 1.469 | Safety-kritisch, viele Verantwortungen |
| 7 | `frontend/src/pages/InspectRun.tsx` | 2.385 | Diagnostics + Rescue + Verify vermischt |
| 8 | `backend/core/dev_dashboard.py` + Cluster | ~4k | DCC-Logik fragmentiert aber zentral schwer |
| 9 | `frontend/src/pages/Dashboard.tsx` | 2.291 | Einstieg mit zu vielen Querschnittsaufgaben |
| 10 | `frontend/src/locales/*.json` | 3.379 | i18n-Monolith für alle Domänen |

---

## Update: Facade Caller Migration A.2–A.4 (2026-06-10)

| Modul | Migration |
|-------|-----------|
| `backend/modules/backup_engine.py` | Safety-Imports → `safety_facade` (**erledigt**) |
| `backend/modules/restore_engine.py` | Safety-Imports → `safety_facade` (**erledigt**) |
| `backend/preflight/backup.py` | Write-Guard → `safety_facade` (**erledigt**) |

**B.1 (erledigt):** `partition_storage_facade.py`, `backup_target_auto_prepare.py`, `inspect/collector.py`

**Phase C.1 (erledigt):** Deploy Runner Registry — `runner_registry.py`  
**Phase C.2 (erledigt):** Result Contract — `runner_result_contract.py`  
**Phase C.3 (erledigt):** API Facade — `runner_api_facade.py`  
**Phase C.4 (erledigt):** Risk Gate — `runner_risk_gate.py`  
115 Runner **noch nicht** migriert oder ausgeführt.

**Nächste Kandidaten:**

**Phase C.5+C.6 (erledigt):** 9 Routen decoupled, Imports 113→104  

1. **C.7** Nächster Routes-Slice
4. B.2: `app.py` Storage-Hilfen, `inspect_storage.py`
5. Router-Extraktion `app.py`
