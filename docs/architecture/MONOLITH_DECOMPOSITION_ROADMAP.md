# Monolith Decomposition Roadmap

**Datum:** 2026-06-10 (aktualisiert nach Deploy Runner Risk Gate C.4)  
**HEAD:** `ef20b6a`+ (C.3 Facade) → C.4 Risk Gate  
**Status:** C.1–C.6 erledigt; **104** direkte Runner-Imports (von 113); Execute gesperrt

## Strategie

- **Kein Big-Bang** — inkrementelle Extraktion mit Facades
- **Router-First** — API-Routen zuerst aus `app.py` lösen (Vorbild: `api/routes/partitions.py`)
- **Runner-Registry** — Deploy-Runner über Registry statt 115 direkter Imports
- **Frontend Feature-Slices** — Pages in `features/{domain}/` zerlegen
- **Contracts vor Code** — OpenAPI + Tests pro extrahiertem Modul

---

## Phase A – API-Monolith auflösen (P1)

### A1: `backend/app.py` Router-Extraktion

| Kandidat | Zielmodul | Status |
|----------|-----------|--------|
| Health/Init/Logs-Path | `api/routes/health.py` | **E.1 erledigt** (3 GET) |
| Version API | `api/routes/version.py` | **E.1 erledigt** (1 GET) |
| Settings/Status GET | `api/routes/settings.py`, `status.py` | **E.2 erledigt** (5 GET) |
| Capabilities/Catalog/Logs | `capabilities.py`, `catalog.py`, `health.py` | **E.3 erledigt** (5 GET) |
| DCC Readonly Indexes | `dev_dashboard_readonly.py` | **E.4 erledigt** (5 GET) |
| DCC Roadmap Registry | `dev_dashboard_roadmap.py` | **E.5/E.6 erledigt** (7 GET) |
| Backup-Routen | `api/routes/backup.py` | offen |
| User/Security | `api/routes/users.py`, `api/routes/security.py` | bestehend |
| System-Info | `api/routes/system.py` | offen |
| Settings | `api/routes/settings.py` | offen |

**Facade:** `app_bootstrap/router_registry.py` — `register_core_routes()` aktivieren  
**Contract:** OpenAPI-Subset-Tests pro Router  
**API-Auswirkung:** Keine URL-Änderung  
**Tests:** Bestehende API-Tests pro Domäne splitten  
**Aufwand:** L (8–15 PRs)

### A2 / C.1: Deploy Runner Registry (**C.1 erledigt**)

| Kandidat | Status | Modul |
|----------|--------|-------|
| 115 `runner_*.py` inventarisieren | **erledigt** | `deploy/runner_registry.py` |
| Statische Klassifikation | **erledigt** | Heuristiken + Evidence-Export |
| Result Contract | **erledigt** (C.2) | `runner_result_contract.py` |
| API Facade read-only | **erledigt** (C.3) | `runner_api_facade.py` + 5 GET-Routen |
| Runner refaktorieren / Lazy-Import | **offen** | C.5 |
| `routes.py` Import-Entlastung | **C.5+C.6** | 104 Imports (9 entfernt) |

**C.1 geliefert:** Metadaten (category, risk_level, execution_policy), Boundary-Warnungen, Tests — **keine** Runner-Ausführung.  
**C.2 geliefert:** `RunnerResult`, Validator, Legacy-Normalizer, Empty-Results — **keine** Runner-Ausführung.  
**C.3 geliefert:** read-only GET `/api/deploy/runners/*` — keine Runner-Ausführung.  
**Nächste Schritte:** C.4 Risk Gate → C.5 Migration  
**Evidence:** `docs/evidence/deploy-runner/`, `docs/architecture/DEPLOY_RUNNER_REGISTRY.md`  
**Aufwand Rest:** L–XL

---

## Phase A.0 – Core Facade Caller (erledigt)

| Datei | Status |
|-------|--------|
| `preflight/backup.py` | **migriert** → `safety_facade` |
| `modules/backup_engine.py` | **migriert** → `safety_facade` |
| `modules/restore_engine.py` | **migriert** → `safety_facade` |

Evidence: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4.md`

Verbleibende Safety-Legacy: `app.py`, `rescue/orchestrator.py`

---

## Phase B – Storage / Classification (P1)

### B1: Storage Caller Migration (**erledigt**)

| Datei | Status |
|-------|--------|
| `backup_target_auto_prepare.py` | **migriert** → `storage_facade` + `safety_facade` |
| `inspect/collector.py` | **migriert** → `storage_facade` + `safety_facade` |
| `partition_storage_facade.py` | **migriert** → `safety_facade` |

Evidence: `CORE_FACADE_STORAGE_MIGRATION_B1.md`

### B2: Verbleibende Storage-Duplikate

| Kandidat | Zielmodul |
|----------|-----------|
| `app.py` Storage-Hilfen | Router + `storage_facade` |
| `inspect_storage.py` | `mount_facade` |
| Deploy Runner Registry | `deploy/runner_registry.py` (**C.1**) — Orchestrierung C.3 |

**Contract:** unverändert  
**Tests:** Facade-Contracts + Domain-Tests  
**Aufwand:** L

### B2: Rescue USB Writer

| Kandidat | Zielmodul |
|----------|-----------|
| `rescue_fat32_esp_usb_writer.py` (1.469 Z.) | `rescue/usb/write_pipeline.py` + `rescue/usb/verify.py` |

**Facade:** `rescue/usb/facade.py` — einziger Schreib-Entry (weiterhin gated)  
**Aufwand:** L

---

## Phase C – Frontend Page-Monolithen (P2)

### C1: BackupRestore.tsx (3.992 Z.)

| Slice | Zielstruktur |
|-------|--------------|
| Wizard-Steps | `features/backup/components/` |
| Manifest-UI | `features/backup/manifest/` |
| API | `features/backup/api.ts` |
| Page | `pages/BackupRestore.tsx` — nur Shell (<300 Z.) |

**Contract:** Bestehende Backup-API  
**Tests:** Vitest Component-Tests pro Slice  
**Aufwand:** L

### C2: ControlCenter + Dashboard

| Kandidat | Ziel |
|----------|------|
| `ControlCenter.tsx` | `features/companion/control-center/` |
| `Dashboard.tsx` | `features/companion/dashboard/` |

**Aufwand:** M je Datei

### C3: Development Control Center

| Kandidat | Ziel |
|----------|------|
| `dev-dashboard/*` + `DevDashboardBody.tsx` | `features/dcc/` mit klarer Public API |

**Facade:** `lib/devDashboard/index.ts` — ein Export  
**Aufwand:** L

---

## Phase D – DCC / Deploy Status (P2)

### D1: Dashboard Status Vereinheitlichung

| Kandidat | Ziel |
|----------|------|
| 6× `dev_dashboard_*.py` | `core/dcc/status_facade.py` |

**Contract:** `CompactStatus`, `CockpitSummary` — JSON-Schema  
**Frontend:** `dccCompactStatus.ts` konsumiert nur Facade-Response  
**Aufwand:** M

---

## Phase E – Daten-Monolithen (P3)

### E1: i18n Namespaces

| Kandidat | Ziel |
|----------|------|
| `locales/de.json` (3.379 Z.) | `locales/de/{backup,partitions,rescue,common}.json` |

**Tooling:** `i18next` Namespace-Loader  
**Aufwand:** M

### E2: Evidence-Aufräumen

| Kandidat | Ziel |
|----------|------|
| `docs/evidence/` (794 MD) | Archivierung + Index-JSON |

**Aufwand:** S (organisatorisch)

---

## Phase F – Betriebs-Monolithen (P3)

### F1: Rescue Build Scripts

| Kandidat | Ziel |
|----------|------|
| `prepare-controlled-live-build-tree.sh` (1.059 Z.) | Unterfunktionen in `scripts/rescue-live/lib/` |

**Aufwand:** M

---

## Migrations-Matrix

| Phase | Domäne | Aufwand | API-Break | Safety-Risk |
|-------|--------|---------|-----------|-------------|
| A1 | Runtime/API | L | Nein | Mittel |
| A2 | Deployment | XL | Nein | Hoch |
| B1 | Storage | M | Nein | **Kritisch** — nur mit Gates |
| B2 | Rescue | L | Nein | **Kritisch** |
| C1 | Backup UI | L | Nein | Niedrig |
| C2 | Companion UI | M | Nein | Niedrig |
| C3 | DCC UI | L | Nein | Niedrig |
| D1 | DCC Backend | M | Nein | Niedrig |
| E1 | i18n | M | Nein | Niedrig |
| F1 | Rescue Scripts | M | Nein | Mittel |

---

## Empfohlene Reihenfolge

1. **A1** — `app.py` Router-Extraktion (Backup, System, Settings) — höchster ROI
2. **B1** — Storage Safety Facade — Duplikat-Risiko senken
3. **C1** — `BackupRestore.tsx` zerlegen — größter Frontend-Monolith
4. **D1** — DCC Status Facade — Deploy-Drift-Transparenz
5. **C.7** — Nächster Routes-Slice (C.6 **erledigt**)
6. **C3** — DCC Frontend-Slice
7. **B2** — Rescue USB Writer Pipeline
8. **E1** — i18n Namespaces
9. **C2** — Companion Dashboards
10. **F1** — Rescue Build Script-Lib

---

## Erfolgskriterien pro Extraktion

- [ ] Keine neue API-URL ohne Versionierung
- [ ] Bestehende Tests grün
- [ ] Fan-In des Monolithen sinkt messbar
- [ ] OpenAPI-Diff leer
- [ ] Phase-0-Gates grün nach Deploy
- [ ] Evidence-Doc für extrahiertes Modul

---

## Update: Phase C.1 Deploy Runner Registry (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| `runner_registry.py` — Contracts + Classifier | **erledigt** |
| Inventar 115 Runner | **erledigt** |
| `generate-deploy-runner-registry.py` | **erledigt** |
| Boundary warn-only (registry policy) | **erledigt** |
| Runner refaktorieren | **nicht** in C.1 |

## Update: Phase C.2 Deploy Runner Result Contract (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| `runner_result_contract.py` | **erledigt** |
| Validator + Legacy-Normalizer | **erledigt** |
| Registry-Integration (empty result) | **erledigt** |
| Pattern-Audit + Boundary C.2 | **erledigt** |
| Runner-Migration | **nicht** in C.2 |

## Update: Phase C.3 Deploy Runner API Facade (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| `runner_api_facade.py` | **erledigt** |
| 5 read-only GET-Routen | **erledigt** |
| 112 Legacy Runner-Imports | **unverändert** |
| Runner-Ausführung | **keine** |

## Update: Phase C.4 Deploy Runner Risk Gate (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| `runner_risk_gate.py` | **erledigt** |
| 5 read-only Risk-Gate GET-Routen | **erledigt** |
| `allowed_to_execute` | **immer false** |
| Runner-Ausführung | **keine** |

## Update: Phase C.5 Routes Decoupling (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| 4 plan-only Routen decoupled | **erledigt** |
| Imports 113→109 | **erledigt** |
| Execute-Freigabe | **nein** |

## Update: Phase C.6 Routes Decoupling (2026-06-10)

| Lieferung | Status |
|-----------|--------|
| 5 evidence/identifier Routen | **erledigt** |
| Imports 109→104 | **erledigt** |
| Execute | **nein** |

**Nächster Schritt:** D.10 versioning Router

---

## Deploy Route Extraction (Phase D)

Nach C.1–C.6 ist `backend/deploy/routes.py` der größte verbleibende Deploy-Monolith (**5041 Zeilen, 237 Routen, 104 Runner-Imports**).

| Phase | Lieferung | Status |
|-------|-----------|--------|
| **D.1** | Domain-Audit, Inventar, Zielarchitektur, Risiko | **erledigt** |
| **D.2** | `routes_registry.py` — 5 GET Facade-Routen | **erledigt** |
| **D.3** | `routes_risk_gate.py` — 5 GET Risk-Gate-Routen — **erledigt** |
| **D.4** | `routes_evidence.py` — 6 POST plan-only (C.5/C.6) — **erledigt** |
| **D.5** | `routes_governance.py` — 3 POST C.5 — **erledigt** |
| **D.6** | Thin-Orchestrator-Target, Guard, D.7+ — **erledigt** |
| **D.7** | Weitere Evidence plan-only — **erledigt** (6 Routen, 12 Evidence gesamt) |
| **D.8** | diagnostics Router — **erledigt** (6 Routen) |
| **D.9** | notifications Router — **übersprungen** (no_safe_slice) |
| **M.1** | Modul-Katalog, Function Ownership, Do-Not-Duplicate — **erledigt** |
| **D.10** | versioning Router — **erledigt** (8 Routen) |
| **D.11** | runtime Router — **erledigt** (8 Routen) |
| **E.1** | app.py Router-Slice — **erledigt** (4 GET, health+version) |
| **E.2** | app.py Router-Slice — **erledigt** (5 GET, settings+status) |
| **E.3** | app.py Router-Slice — **erledigt** (5 GET) |
| **E.4** | app.py Router-Slice — **erledigt** (5 DCC index GET) |
| **E.5** | app.py Router-Slice — **erledigt** (5 roadmap registry GET) |
| **E.6** | app.py Router-Slice — **erledigt** (2 roadmap next-prompt GET) |
| **E.7** | app.py Router-Slice **Kandidaten-Audit** — **erledigt** (187 Routen gescannt, 3 E.8-Kandidaten) |
| **E.8** | app.py Router-Slice — **erledigt** (3 DCC read-only GET → `dev_dashboard_readonly`) |
| **F.1** | DCC Status Facade — **erledigt** (`core/dcc_status_facade.py`) |
| **F.2** | DCC Router-Migration auf `dcc_status_facade` — **erledigt** (6 GET) |
| **F.3** | DCC Aggregation Audit & Duplicate Status Analysis | **erledigt** |
| **F.4** | DCC Delegation Cleanup (ai_prompt + readonly) | **erledigt** |
| **G.1** | System Status Facade — **erledigt** (`core/system_status_facade.py`) |
| **G.1b** | `/api/system/status` Router-Migration | **erledigt** |
| **G.2b** | `/api/status` network + `/api/system/network` Router-Migration | **erledigt** |
| **G.3** | Network/Core Cleanup (`get_system_info`, `webserver_status`) | **erledigt** |
| **G.4** | Network Handler Extraction — **erledigt** (`api/routes/network.py`, 2 GET) |
| **H.1** | Frontend Status ViewModel Facade — **erledigt** (`viewmodels/statusViewModel.ts`) |
| **H.2** | Frontend Status Utility-Migration — **erledigt** |
| **H.3** | Frontend Status Component Migration (3 Slice) — **erledigt** |
| **H.4** | Frontend Status Component Migration (zweiter 3-Slice) — **erledigt** |
| **H.5** | Frontend Status Utility Migration (3 Libs) — **erledigt** |
| **H.6** | Frontend Status Presentation Migration (5 Slice) — **erledigt** |
| **H.7** | Frontend Status Final Safe Slice — **erledigt** (`count_10`) |
| **G.5** | Network Legacy Elimination Audit — **erledigt** (kein Refactoring) |
| **G.7** | Webserver Status Facade — **erledigt** (`webserver_status_facade`, G.5-Bypass beseitigt) |
| **G.6** | System Info Facade — **erledigt** (`system_info_facade`, G.3-Network delegiert) |
| **G.9** | Hardware Discovery Core — **erledigt** (`hardware_discovery`, Facade→app-Zyklus beendet) |
| **G.8** | Network Discovery Core — **erledigt** (`network_discovery`, Facade-Zyklus beendet) |
| **G.11** | Webserver Service Discovery Core — **erledigt** (`webserver_service_discovery`, Facade→app-Zyklus beendet) |
| **G.12** | System Status Core — **erledigt** (`system_status_core`, Ampel aus Facade) |
| **P.1** | Storage Discovery Canonical — **erledigt** (`storage_discovery`, `storage_facade`-Delegation; `app.py` offen) |
| **D.12** | Deploy Thin-Orchestrator Audit — **erledigt** (Audit + Final Plan; keine Execute-Extraktion) |

Evidence: `docs/evidence/deploy-runner/DEPLOY_ROUTE_DOMAIN_AUDIT_D1.md`  
Architektur: `docs/architecture/DEPLOY_ROUTE_TARGET_ARCHITECTURE_D1.md`  
Modul-Katalog: `docs/architecture/MODULE_CATALOG.md`, `FUNCTION_OWNERSHIP_MATRIX.md`, `DO_NOT_DUPLICATE_RULES.md`
