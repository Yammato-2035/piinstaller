# Post-Decomposition Audit — Phase G.10

**Datum:** 2026-06-10  
**Branch:** `main`  
**HEAD (committed):** `23462c1`  
**Workspace:** enthält uncommittete G.6/G.9-Arbeit (Facade/Cores) — Metriken unten aus **aktuellem Workspace**  
**Modus:** Analyse only — keine Refactorings, keine Migrationen

---

## Phase 0 — Gates

| Gate | Ergebnis |
|------|----------|
| `git branch` | `main` |
| `git rev-parse --short HEAD` | `23462c1` |
| `check-module-boundaries.sh` | `status: review_required` |
| Boundary-Warnungen gesamt | **109** |
| `app.py` Zeilen (Skript) | **16.374** |
| `include_router` in app | **27** |

---

## Phase 1 — Monolith Re-Scan

### 1.1 Backend-Monolithen (Größe)

| Modul | Zeilen | Routen/Imports | Status |
|-------|--------|----------------|--------|
| `backend/app.py` | **16.374** | **182** `@app.*` Routen | LEGACY-Hauptmonolith |
| `backend/deploy/routes.py` | **4.119** | **190** `@router.*`, **81** Runner-Imports | LEGACY-Orchestrator |
| `backend/core/dev_dashboard.py` | 1.217 | Aggregation | CANONICAL, groß |
| `backend/core/rescue_fat32_esp_usb_writer.py` | 1.469 | Rescue-Schreibpfad | CANONICAL, groß |
| `backend/core/rescue_iso_build_state.py` | 1.021 | Rescue-State | CANONICAL |
| `backend/core/safe_device.py` | 993 | Geräte-Grenzen | PARTIAL (app-Kopplung) |
| `backend/core/hardware_discovery.py` | 872 | G.9 neu | CANONICAL |
| `backend/core/system_info_facade.py` | 438 | 1 HTTP-Delegat | CANONICAL (G.6/G.9) |

**Fortschritt seit G.6-Baseline (committed):** `app.py` von ~16.927 → **16.374** (−553 Zeilen durch Hardware-Extraktion + System-Info-Handler-Slice im Workspace).

### 1.2 `app.py` — verbleibende Routen-Domains

| Domain | Routen | Bewertung |
|--------|--------|-----------|
| `/api/control-center` | 33 | Größter verbleibender Block |
| `/api/backup` | 31 | Backup/Restore-Monolith im Handler |
| `/api/dev-dashboard` | 25 | Teilweise nach E.4–E.8 migriert |
| `/api/system` | 20 | Teilweise Facades (status, network, system-info) |
| `/api/radio` | 12 | Feature-Monolith |
| `/api/security` | 8 | Feature-Monolith |
| `/api/raspberry-pi` | 7 | Pi-Konfiguration |
| Sonstige | ≤5 je | install, webserver, presets, … |

**Bereits extrahierte Router (27 `include_router`):** health, version, network, settings, status, capabilities, catalog, dev_dashboard_readonly, dev_dashboard_roadmap, diagnosis, rescue, partition, deploy, inspect, safety, preflight, …

### 1.3 Legacy-Wrapper in `app.py`

| Kategorie | Anzahl | Ziel |
|-----------|--------|------|
| **hardware_discovery** (G.9) | **17** | `get_cpu_*`, `get_ram_info`, `_get_pci_*`, `_get_pi_config_module`, … |
| **network_discovery** (G.8) | **3** | `get_network_info`, `_demo_network`, `_detect_frontend_port` |
| **`run_command` direkte Aufrufe** | **~102** | Zentraler Monolith-Helper, nicht extrahiert |

### 1.4 Facade→Monolith-Zyklen

| Facade | `import app` | Status nach G.8/G.9 |
|--------|-------------|---------------------|
| `network_info_facade` | **nein** | ✅ Zyklus beendet (→ `network_discovery`) |
| `system_info_facade` | **nein** | ✅ Zyklus beendet (→ `hardware_discovery`) |
| `webserver_status_facade` | **ja** (5× `_legacy_*`) | ❌ offen — `get_running_services`, `get_installed_apps`, `run_command`, … |
| `system_status_facade` | **ja** (5× `_legacy_*`) | ❌ offen — `_compute_system_status`, `APP_SETTINGS`, `UserProfile`, Version |

**Verbleibende Zyklen: 2** (Webserver-Services, System-Status/Ampel).

### 1.5 Direkte Core-Kopplungen (Boundary-Auszug)

| Warnung | Ort | Bedeutung |
|---------|-----|-----------|
| `dcc_direct_build_dashboard_status_outside_facade` | `dev_dashboard_cockpit.py` | Cockpit baut Status ohne vollständige Facade-Delegation |
| `dcc_status_router_bypasses_facade` | `dev_dashboard_roadmap.py` | Roadmap-Router umgeht `dcc_status_facade` |
| `dcc_deploy_core_cross_coupling` | `deploy_job_state.py` | Deploy-State ↔ DCC verknüpft |
| `facade_boundary_safe_device` | `app.py` | `safe_device`-Grenze noch im Monolith |
| `system_status_new_network_logic_outside_network_facade` | `app.py` | Rest-Netzwerklogik im Monolith |
| `network_legacy_function_remaining` ×3 | `app.py` | Bewusste Wrapper (G.8) |

### 1.6 Duplicate Candidates (Boundary)

| Muster | Treffer | Domäne |
|--------|---------|--------|
| `duplicate_lsblk_usage` | 11 | Partitions/Storage |
| `duplicate_findmnt_usage` | 8 | Mount/Backup |
| `duplicate_blkid_usage` | 5 | Storage-ID |
| `duplicate_runner_result_status` | 11 | Deploy-Runner |
| `duplicate_mount_logic` | 2 | Mount |
| `duplicate_write_target_validation` | 2 | Safety/Write |
| `duplicate_storage_discovery` | 1 | Storage |
| `dcc_duplicate_ampel_status_mapping` | 1 | `runner_result_contract.py` |

### 1.7 Frontend — große Seiten

| Seite | Zeilen | Risiko |
|-------|--------|--------|
| `BackupRestore.tsx` | **3.992** | Domain-Monolith + lokales Status-Mapping |
| `ControlCenter.tsx` | **2.681** | Control-Center-UI + API-Orchestrierung |
| `InspectRun.tsx` | 2.385 | Diagnose/Inspect |
| `Dashboard.tsx` | 2.291 | Polling, System-Info |
| `Documentation.tsx` | 2.055 | Doku-Embedded-Monolith |
| `SettingsPage.tsx` | 1.716 | Settings |
| `PeripheryScan.tsx` | 994 | Hardware-UI |
| `SecuritySetup.tsx` | 985 | Security |

**Frontend Status:** H.1–H.7 abgeschlossen; **10** verbleibende Domain-Status-Mappings (`frontend_domain_status_mapping_requires_domain_facade`).

### 1.8 Boundary-Warnungen nach Kategorie (Top)

| Kategorie | Anzahl |
|-----------|--------|
| `runner_result_no_evidence_reference` | 35 |
| `frontend_component_local_status_mapping` | 6 |
| Deploy/routes Größe + Runner-Imports | je 1 (plus Reduktions-Historie) |
| `network_legacy_function_remaining` | 3 |
| DCC/Frontend Domain-Facade | 4+6 |

**G.8/G.9-spezifisch:** keine Treffer mehr für `system_info_facade_depends_on_app` / `hardware_discovery_core_missing` (Workspace).

---

## Phase 2 — TOP 20 Restprobleme

### CRITICAL

| # | Problem | Modul | Größe | Risiko | Aufwand | Phase |
|---|---------|-------|-------|--------|---------|-------|
| 1 | **app.py Hauptmonolith** | `backend/app.py` | 16.374 Z / 182 Routen | Jede Änderung regressionsanfällig; 102× `run_command` | XL | **E.9+** Router-Slices (backup, control-center read) |
| 2 | **deploy/routes.py Orchestrator** | `backend/deploy/routes.py` | 4.119 Z / 81 Runner-Imports | Execute/Rescue-Gates vermischt | XL | **D.12–D.15** Thin-Orchestrator |
| 3 | **Backup/Restore API-Monolith** | `app.py` `/api/backup` | 31 Routen | Datenverlust-Risiko bei Refactor ohne Gates | L | **B.1** Backup-Router-Slice + Facade |
| 4 | **Control-Center API-Monolith** | `app.py` `/api/control-center` | 33 Routen | Zentrale Ops-UI gekoppelt | L | **E.9** control-center Router |

### HIGH

| # | Problem | Modul | Größe | Risiko | Aufwand | Phase |
|---|---------|-------|-------|--------|---------|-------|
| 5 | **webserver_status_facade→app Zyklus** | `webserver_status_facade.py` | 5 `_legacy_*` | Facade nicht testbar ohne app | M | **G.11** Service-Discovery Core |
| 6 | **system_status_facade→app Zyklus** | `system_status_facade.py` | 5 `_legacy_*` | Ampel/Backup-State aus Monolith | M | **G.12** System-Status Core |
| 7 | **Storage-Discovery-Duplikate** | lsblk/findmnt/blkid | 24 Treffer | Inkonsistente Partition-Ergebnisse | M | **P.1** Storage-Discovery Canonical |
| 8 | **BackupRestore.tsx** | Frontend | 3.992 Z | UI+Logik+Status vermischt | L | **I.1** Page-Decomposition |
| 9 | **Rescue-Core-Größe** | `rescue_*` cores | 1.4k+ Z | Rescue-Stick-Pfad komplex | M | **R.1** Rescue Route/Core-Slice |
| 10 | **safe_device in app.py** | `app.py` + `safe_device.py` | 993 Z Core | Boundary-Warnung `facade_boundary_safe_device` | M | **S.1** Safe-Device Router/Facade |

### MEDIUM

| # | Problem | Modul | Größe | Risiko | Aufwand | Phase |
|---|---------|-------|-------|--------|---------|-------|
| 11 | **DCC Cockpit Status-Aggregation** | `dev_dashboard_cockpit.py` | 731 Z | Parallele Status-Logik | M | **F.5** Cockpit→`dcc_status_facade` |
| 12 | **DCC Roadmap Router Bypass** | `dev_dashboard_roadmap.py` | — | Facade-Regel verletzt | S | **F.6** Roadmap Facade-Compliance |
| 13 | **Runner Evidence Lücken** | deploy runners | 35 Warnungen | Governance/CI-Drift | M | **D.13** Runner Evidence Gate |
| 14 | **Network Legacy Wrapper in app** | 3 Funktionen | — | API-Stabilität OK, technische Schuld | S | **G.13** Wrapper-Abbau (optional) |
| 15 | **ControlCenter.tsx** | Frontend | 2.681 Z | Wartbarkeit | M | **I.2** Control-Center ViewModels |
| 16 | **Notifications Router (D.9)** | deploy | übersprungen | Fehlendes READ-Modul | M | **D.9** notifications Router |
| 17 | **Domain Status Mapping (Frontend)** | 10 Komponenten | count_10 | Ampel-Duplikate Partition/Safety | M | **I.3** Domain Status Facades |
| 18 | **dev_dashboard.py Größe** | Core | 1.217 Z | DCC-Monolith im Core | M | **F.7** DCC Core-Split |

### LOW

| # | Problem | Modul | Größe | Risiko | Aufwand | Phase |
|---|---------|-------|-------|--------|---------|-------|
| 19 | **include_router 27** | `app.py` | 27 Router | Bootstrap-Komplexität | S | **E.10** Bootstrap-Registry Cleanup |
| 20 | **Feature-Setup-Monolithen** | radio/security/nas routes | 12–8 Routen | Isoliert, geringe Kreuzkopplung | S | **E.11+** Feature-Router (nach Kernpfaden) |

---

## Phase 3 — Empfohlene Roadmap-Reihenfolge (G.10)

Priorität nach **Risiko × Nutzen × Abhängigkeiten** — ersetzt keine committed Roadmap, ergänzt sie.

### Architektur (Backend-Monolith-Abbau)

1. **G.11** — Webserver Service Discovery Core (`webserver_status_facade` entkoppeln)
2. **G.12** — System Status Core (`system_status_facade` entkoppeln)
3. **E.9** — `control-center` Router-Slice (33 Routen)
4. **B.1** — `backup` Router-Slice + Backup-State-Facade (31 Routen)
5. **D.12** — `deploy/routes.py` weiter verdünnen (<3000 Z Zwischenziel)

### Rettungsstick (Rescue)

6. **R.1** — Rescue ISO Build / Executor Route-Nähe zu Cores prüfen, HTTP-Slice
7. **R.2** — Rescue Telemetry + Agent Ingest Router-Konsolidierung
8. **R.3** — `rescue_fat32_esp_usb_writer` Write-Gate-Dokumentation (kein Read/Write-Mix)

### Partitionshelfer

9. **P.1** — Storage Discovery Canonical (lsblk/findmnt/blkid-Dedup)
10. **P.2** — Partition Router aus `app.py` (`/api/partitions` bereits Router — app-Reste abbauen)
11. **S.1** — `safe_device` Facade-Boundary schließen

### Diagnoseserver / Deploy

12. **D.13** — Runner Evidence Reference Gate (35 Warnungen)
13. **D.9** — Notifications Router (wenn safe slice verfügbar)
14. **D.14** — Deploy Execute-Gate vs. Read-Trennung finalisieren

### DCC

15. **F.5** — `dev_dashboard_cockpit` → volle `dcc_status_facade`-Delegation
16. **F.6** — `dev_dashboard_roadmap` Facade-Compliance
17. **F.7** — `dev_dashboard.py` Core-Split (modules vs. status)

### Frontend

18. **I.1** — `BackupRestore.tsx` Zerlegung (größte Seite)
19. **I.2** — `ControlCenter.tsx` ViewModel/API-Client-Slice
20. **I.3** — Domain Status Facades (Partition/Safety/Backup — 10 Mappings)

---

## Phase 4 — Zusammenfassung G.8/G.9 Wirkung

| Vorher (pre-G.8/G.9) | Nachher (Workspace) |
|----------------------|---------------------|
| `network_info_facade` → lazy `import app` | → `network_discovery` ✅ |
| `system_info_facade` → 17× `_legacy_*` → `app` | → `hardware_discovery` ✅ |
| Facade→app-Zyklen: **4** | Verbleibend: **2** (webserver, system_status) |
| Hardware-Logik in `app.py` | Extrahiert nach `hardware_discovery.py` (872 Z) |
| `app.py` Handler system-info ~240 Z | 6 Z Wrapper |

**Nicht erreicht (bewusst out of scope G.8/G.9):** `app.py` Gesamtgröße, `deploy/routes.py`, Backup/Control-Center-Routen, Frontend-Monolithen.

---

## Empfohlene nächste 10 Phasen (Kurzliste)

| Nr | Phase | Fokus |
|----|-------|-------|
| 1 | **G.11** | Webserver Service Discovery Core |
| 2 | **G.12** | System Status Core |
| 3 | **P.1** | Storage Discovery Dedup (Partitions) |
| 4 | **E.9** | control-center Router-Slice |
| 5 | **B.1** | backup Router-Slice |
| 6 | **F.5** | DCC Cockpit Facade-Delegation |
| 7 | **D.12** | deploy/routes.py Thin-Orchestrator Fortsetzung |
| 8 | **R.1** | Rescue HTTP/Core-Slice |
| 9 | **I.1** | BackupRestore.tsx Decomposition |
| 10 | **D.13** | Runner Evidence Reference Gate |

---

## Anhang — Metrik-Snapshot

```json
{
  "head": "23462c1",
  "branch": "main",
  "boundary_status": "review_required",
  "boundary_warnings": 109,
  "app_py_lines": 16374,
  "app_py_routes": 182,
  "deploy_routes_lines": 4119,
  "deploy_runner_imports": 81,
  "legacy_wrappers_hardware": 17,
  "legacy_wrappers_network": 3,
  "facade_app_cycles_remaining": 2,
  "facade_app_cycles_closed_g8_g9": 2,
  "run_command_calls_app": 102,
  "frontend_largest_page": "BackupRestore.tsx:3992"
}
```

**Evidence-Quellen:** `./scripts/check-module-boundaries.sh`, Workspace-Line-Counts, `MODULE_CATALOG.md`, `MONOLITH_DECOMPOSITION_ROADMAP.md`, G.6/G.9 Audit-Artefakte.
