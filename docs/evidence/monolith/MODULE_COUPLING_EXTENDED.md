# Module Coupling Analysis (Extended)

**Datum:** 2026-06-10  
**HEAD:** `9005c54`

## Fan-In (wer wird am häufigsten referenziert)

| Modul | Fan-In (grep-approx) | Rolle |
|-------|----------------------|-------|
| `app.py` / `app` | **470** | Zentraler Hub — alle Domänen |
| `dev_dashboard` | 32 | DCC-Cluster |
| `safe_device` | 17 | Storage Safety |
| `deploy_manifest` | 14 | Deploy Drift |
| `notification_service` | 11 | Notifications |
| `backup_engine` | 8 | Backup |
| `profile_deploy_manifest` | 8 | Profile Gate |
| `partition_hardstop` | 6 | Partitions Safety |
| `storage_role_classification` | 3 | Partitions (gut isoliert) |

## Fan-Out (wer importiert am meisten)

| Modul | Imports (ca.) | Bewertung |
|-------|---------------|-----------|
| `backend/app.py` | **50+** direkte Imports | CRITICAL — God Object |
| `backend/deploy/routes.py` | 40+ Runner-Imports | CRITICAL |
| `frontend/src/pages/BackupRestore.tsx` | 30+ | HIGH |
| `frontend/src/App.tsx` | 25+ Page-Imports | HIGH (Router-Monolith) |

## Zyklische Abhängigkeiten (beobachtet)

| Zyklus | Beschreibung | Risiko |
|--------|--------------|--------|
| `app.py` ↔ `modules/*` | App ruft Module, Module erwarten App-Kontext | HIGH |
| `dev_dashboard.py` ↔ `deploy_manifest.py` | Status braucht Deploy, Deploy-Runner brauchen DCC-Status | MEDIUM |
| `core/rescue_*` ↔ `deploy/runner_rescue_*` | Rescue-Core und Deploy-Runner teilen State-Dateien | HIGH |
| Frontend Pages ↔ `lib/devDashboard/*` ↔ `api.ts` | Bidirektionale Status-Transformation | MEDIUM |

## Domain-Leaks (Cross-Domain-Imports)

| Von | Nach | Leak |
|-----|------|------|
| `app.py` | `modules/backup`, `modules/storage_detection`, `core/rescue_*` | Backup + Rescue + Runtime in einer Datei |
| `deploy/routes.py` | Rescue-Runner, Laptop-Gates, Identifier-Cleanup | Deploy-Orchestrator = Meta-Domäne |
| `control_center.py` | Monitoring, NAS, Backup-Status | Companion aggregiert alles |
| `BackupRestore.tsx` | Partition-Hints, Verify, Manifest-UI | Backup-Page kennt Storage |
| `Dashboard.tsx` | Dev-Dashboard-Links, Backup, Security | Startseite = Router zu allem |

## Direkte Systemzugriffe (Umgehung Core)

| Muster | Vorkommen | Domäne |
|--------|-----------|--------|
| `subprocess.run` / `os.system` in `app.py` | Viele | Runtime |
| `subprocess` in Deploy-Runnern | 115 Dateien | Deployment |
| Direktes `open()` für Config in Pages | Frontend Settings | Runtime |
| `pwd`, `psutil` in `app.py` | Systeminfo | Runtime |

**Empfehlung:** `core/system_facade.py` für OS-Zugriffe (teilweise fehlt).

## Kopplungs-Heatmap nach Domäne

```
                    app.py
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
 backup          rescue            deploy/routes
    │                 │                 │
modules/*      core/rescue_*     runner_* (115)
    │                 │                 │
safe_device    fat32_writer      manifest/drift
```

## Isolierte Module (gutes Vorbild)

| Modul | Fan-In | Bewertung |
|-------|--------|-----------|
| `storage_role_classification.py` | 3 | Gut — klare API, Tests |
| `backend/api/routes/partitions.py` | niedrig | Gut — extrahiert |
| `partitionApi.ts` | niedrig | Gut — dünner Client |
| `app_bootstrap/*` | niedrig | Gut — Migration begonnen |

## Kopplungs-Risiko-Zusammenfassung

| Risiko | Ursache |
|--------|---------|
| **CRITICAL** | `app.py` als einziger Integrationspunkt für 15+ Domänen |
| **CRITICAL** | `deploy/routes.py` koppelt Deploy an Rescue, Verify, Governance |
| **HIGH** | Frontend Pages importieren quer über Domänen-Grenzen |
| **MEDIUM** | DCC-Status-Cluster ohne klare Facade |
| **LOW** | Partitionshelfer nach Phase 3.0 Workbench entkoppelt |

## Empfohlene Entkopplungs-Hebel

1. **Router-Extraktion** aus `app.py` → `api/routes/{domain}.py` (Partitions-Vorbild)
2. **Deploy-Runner-Registry** — C.1–C.3 erledigt; `routes.py` Fan-In CRITICAL bis C.5
3. **Domain-Facades** in `core/{domain}_facade.py` — nur Facades von außen importierbar
4. **Frontend Feature-Slices** — `features/backup/`, `features/rescue/` statt Page-Monolithen
5. **Event-Bus light** für DCC-Status statt direkter Cross-Imports

---

## Update: Facade Caller Migration A.2–A.4 (2026-06-10)

| Kante | Vorher | Nachher |
|-------|--------|---------|
| `preflight/backup` → `write_guard` | direkt | über `safety_facade` |
| `backup_engine` → `safe_device` | direkt | über `safety_facade` |
| `restore_engine` → `safe_device` | direkt | über `safety_facade` |

`safe_device` Fan-In sinkt für Produkt-Engines; Implementierungskern bleibt in `safe_device.py` + `safety_facade.py`.

Nächste Kandidaten: `app.py`, `inspect_storage.py`.

---

## Update: Deploy Runner Registry C.1 (2026-06-10)

| Kante | Status |
|-------|--------|
| `deploy/routes.py` → 115 `runner_*` Imports | unverändert (kein Refactoring) |
| Statische Runner-Metadaten | **neu** — `runner_registry.py` + Boundary warn-only |
| `routes.py` Fan-In | bleibt CRITICAL bis C.3 API Facade |

Evidence: `docs/evidence/deploy-runner/runner_registry.generated.json`

**C.2 (erledigt):** Result Contract — `runner_result_contract.py`, keine `routes.py`-Entkopplung yet.

**C.3 (erledigt):** read-only API Facade — 112 direkte Imports in `routes.py` unverändert.

**C.4 (erledigt):** Risk Gate — Entscheidungen ohne Execute.

**C.5+C.6 (erledigt):** 9 Imports aus `routes.py` entfernt (104 verbleibend).

**D.2 (erledigt):** `routes_registry.py` entkoppelt (5 GET, Facade-only).

**D.5 (erledigt):** `routes_governance.py` (3 POST). Facade nur in Subroutern.

**D.9 (übersprungen):** no_safe_d9_notifications_slice — 0 Routen, kein Router.

**M.1 (erledigt):** Modul-Katalog — 12 Pflichtmodule, 30 Ownership-Zeilen, Boundary-Guard WARN-only (duplicate_* checks).

**D.10 (erledigt):** `routes_versioning.py` — 8 Routen, routes.py 89 Runner-Imports.

**D.11 (erledigt):** `routes_runtime.py` — routes.py 81 Runner-Imports.

**E.1 (erledigt):** `api/routes/health.py` + `version.py` — 4 GET.

**E.2 (erledigt):** `api/routes/settings.py` + `status.py` — 5 GET, app.py 17.779→17.699.

**E.3 (erledigt):** `capabilities.py`, `catalog.py` + Erweiterung health/status — 5 GET, app.py 17.699→17.617.

**E.4 (erledigt):** `dev_dashboard_readonly.py` — 5 DCC index GET, app.py 17.617→17.568.

**E.5 (erledigt):** `dev_dashboard_roadmap.py` — 5 GET, app.py 17.568→17.499.

**E.6 (erledigt):** `dev_dashboard_roadmap.py` +2 Routen, app.py 17.499→17.472.

**Nächster Schritt:** E.7

---

## Update: Storage Facade Migration B.1 (2026-06-10)

| Kante | Status |
|-------|--------|
| `backup_target_auto_prepare` → blkid | über `storage_facade` |
| `inspect/collector` → `storage_detection` | über `storage_facade` |
| `partition_storage_facade` → `write_guard` | über `safety_facade` |
