# Monolith Decomposition Roadmap

**Datum:** 2026-06-10 (aktualisiert nach Deploy Runner Risk Gate C.4)  
**HEAD:** `ef20b6a`+ (C.3 Facade) → C.4 Risk Gate  
**Status:** C.1–C.4 erledigt; 112 Legacy-Imports; Execute weiterhin gesperrt

## Strategie

- **Kein Big-Bang** — inkrementelle Extraktion mit Facades
- **Router-First** — API-Routen zuerst aus `app.py` lösen (Vorbild: `api/routes/partitions.py`)
- **Runner-Registry** — Deploy-Runner über Registry statt 115 direkter Imports
- **Frontend Feature-Slices** — Pages in `features/{domain}/` zerlegen
- **Contracts vor Code** — OpenAPI + Tests pro extrahiertem Modul

---

## Phase A – API-Monolith auflösen (P1)

### A1: `backend/app.py` Router-Extraktion

| Kandidat | Zielmodul | Zielstruktur |
|----------|-----------|--------------|
| Backup-Routen | `api/routes/backup.py` | `backend/api/routes/` |
| User/Security | `api/routes/users.py`, `api/routes/security.py` | bestehend |
| System-Info | `api/routes/system.py` | `core/system_info_service.py` |
| Settings | `api/routes/settings.py` | `core/settings_facade.py` |

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
| `routes.py` Import-Entlastung | **teilweise** | 112 Imports bleiben |

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
5. **C.5** — Runner Migration (C.1–C.4 **erledigt**)
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

**Nächster Schritt:** C.5 schrittweise Runner-Migration
