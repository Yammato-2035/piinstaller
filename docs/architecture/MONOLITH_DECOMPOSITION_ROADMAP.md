# Monolith Decomposition Roadmap

**Datum:** 2026-06-10 (aktualisiert nach Facade Caller A.2–A.4)  
**HEAD:** `42fb673`+ (siehe Commit `arch(core): migrate backup restore callers to safety facade`)  
**Status:** Phase A.1 Facade Freeze + **A.2–A.4 Safety-Caller migriert**; Router/Storage-Monolith offen

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

### A2: `backend/deploy/routes.py` Runner-Registry

| Kandidat | Zielmodul | Zielstruktur |
|----------|-----------|--------------|
| 115 `runner_*.py` | `deploy/registry.py` | Lazy-Import-Registry |
| Route-Handler | `deploy/handlers/` | Gruppiert nach Domäne |

**Facade:** `deploy/orchestrator.py` — ein Entry für DCC  
**Contract:** Runner-Metadaten (id, domain, profile, dry_run)  
**API-Auswirkung:** Keine  
**Tests:** Registry-Unit-Tests + Smoke pro Runner-Gruppe  
**Aufwand:** XL (mehrere Sprints)

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
| Deploy Runner Registry | `deploy/registry.py` |

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
5. **A2** — Deploy Runner Registry — Wartbarkeit
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
