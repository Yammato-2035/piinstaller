# Architektur-FAQ — Core Facades (DE)

Kurzantworten zu Storage/Mount/Safety-Facades (Phase A.1 + Caller-Migration A.2–A.4). Keine Produktwerbung.

## Was sind Core Facades?

Drei Module unter `backend/core/`: `storage_facade`, `mount_facade`, `safety_facade`. Sie sind die **kanonische Schnittstelle** für Geräteerkennung, Mount-Pläne und Schreibziel-Prüfungen.

## Warum gibt es sie?

Im Monolith-Audit wurden viele Duplikate gefunden (`lsblk` in `app.py`, `safe_device`, Rescue, Deploy-Runner). Facades verhindern, dass jedes neue Modul dieselbe Logik erneut baut.

## Was wurde in A.1 geändert?

- Öffentliche Contracts (Datentypen + Funktionen)
- Dokumentation und Inventar
- Warn-only Boundary-Check
- Unit-Tests für Contracts

**Nicht** geändert: bestehende APIs, Runtime-Verhalten, Legacy-Imports.

## Darf ich weiterhin `safe_device` direkt importieren?

**Legacy:** ja, bestehender Code bleibt. **Neue Module:** nein — nur Facades (siehe `CORE_FACADE_RULES.md`).

## Führt die Mount-Facade echte Mounts aus?

Nein. `build_readonly_mount_plan` und Validatoren sind **plan-only** / Analyse.

## Welche Safety-Kontexte gibt es?

`live`, `rescue`, `partition_helper`, `cloudserver_future` (`SafetyContext` in `safety_facade.py`).

## Wann blockiert der Boundary-Check?

Aktuell **nur Warnungen** in `check-module-boundaries.sh`. CI-Block ist für eine spätere Phase vorgesehen.

## Was wurde in A.2–A.4 migriert?

`preflight/backup.py`, `backup_engine.py` und `restore_engine.py` importieren Safety nur noch über `core.safety_facade`. Fehlercodes und Verhalten sind unverändert (Delegation).

## Warum wird `app.py` nicht sofort zerlegt?

~18k Zeilen, ~213 Routen — Router-Extraktion erfordert eigene Phase B mit OpenAPI-Parität. Safety-Migration der Engines war isolierbar und risikoarm.

## Warum bleibt der Boundary Guard teilweise warn-only?

`app.py`, Deploy-Runner und Storage-Legacy sind noch nicht migriert. Verschärfte Prüfung gilt bereits für die drei migrierten Safety-Caller.

## Ändert sich das Backup- oder Restore-Verhalten?

**Nein** — gleiche `safe_device`/`write_guard`-Logik, nur zentraler Importpfad. Keine neuen Zielpfade, keine abgeschwächten Gates.

## Warum ist das sicherer?

Weniger verstreute Imports → weniger Risiko, dass neue Module eigene Safety-Logik bauen. Boundary Guard erkennt Rückfälle in migrierten Dateien.

## Was wurde in B.1 migriert?

blkid/Storage-Erkennung in `backup_target_auto_prepare` und `inspect/collector` läuft über `storage_facade`. `partition_storage_facade` nutzt `safety_facade` statt direktem `write_guard`.

## Was ist die Deploy Runner Registry (C.1)?

Statisches Inventar und Metadaten für **115** `runner_*.py` unter `backend/deploy/`. Modul: `runner_registry.py`. **Keine** Runner-Ausführung, **kein** Refactoring der Runner selbst.

## Was ist der Runner Result Contract (C.2)?

Einheitliches Ergebnisschema (`RunnerResult`) mit 6 Statuswerten, `warnings`/`errors`, `evidence_paths` und `no_execution_performed`. Modul: `runner_result_contract.py`. Legacy-Dicts werden per `normalize_legacy_runner_result` abbildbar — Runner selbst unverändert.

## Warum werden Runner nicht sofort refaktoriert?

Größtes Risiko-Cluster (~37k Zeilen). C.1 + C.2 liefern Metadaten und Result-Contract. C.3–C.5: API Facade, Risk Gate, schrittweise Migration.

## Was ist die Deploy Runner API Facade (C.3)?

Read-only Schicht `runner_api_facade.py` + **5 GET-Routen** unter `/api/deploy/runners/*`. Listet Registry/Contract — **keine** Runner-Ausführung. Die 112 direkten Runner-Imports in `routes.py` bleiben vorerst.

## Was ist das Deploy Runner Risk Gate (C.4)?

`runner_risk_gate.py` wertet `risk_level`, `execution_policy` und optional Operator-Kontext aus. **`allowed_to_execute` bleibt immer false** — nur Planungsentscheidungen für C.5.

## Was wurde in C.5/C.6 decoupled?

**C.5:** 4 Routen (Version/Identifier/Next-Phase). **C.6:** 5 Evidence/Identifier-Routen. **113→104** Imports. `facade_decoupling_c5/c6`, Execute weiterhin false.

## Was ist Phase D.1 (Route Domain Audit)?

Vollständige Domänenanalyse von `backend/deploy/routes.py` (**5041 Zeilen, 237 Routen**) ohne Refactoring. Lieferung: Inventar, Domain-Matrix, Zielarchitektur, Extraktionsrisiko. **Keine** Router verschoben, **keine** API geändert.

## Warum Domain-Aufteilung statt Big-Bang?

OpenAPI/DCC-Stabilität, CRITICAL Execute-Routen zuletzt. Inkrementell: Registry → Risk Gate → Evidence → Governance → Runtime/Rescue.

## Warum Registry/Risk Gate zuerst extrahieren (D.2/D.3)?

Beide nutzen nur `runner_api_facade` — **0** direkte `runner_*`-Imports in den Handlern. Niedrigstes Risiko.

## Warum Execute-Routen zuletzt?

`/execute`, `/write/execute`, `real-write` sind **CRITICAL** — erfordern Operator-Gates und E2E vor physischer Extraktion.

## Was ist Phase D.2 (Registry Router)?

5 GET-Routen (`/runners/catalog`, `/summary`, `/policy-warnings`, `/{runner_id}`, `/{runner_id}/empty-result`) nach `routes_registry.py` ausgelagert. Pfade unverändert, nur Facade, kein Runner-Execute.

## Was ist Phase D.3 (Risk-Gate-Router)?

5 GET-Routen (`/runners/risk-gate/*`, `/{runner_id}/risk-gate`) nach `routes_risk_gate.py`. Nur Facade, `allowed_to_execute` bleibt false.

## Was ist Phase D.4 (Evidence-Router)?

6 POST plan-only Routen (C.5/C.6 Identifier/Evidence) nach `routes_evidence.py`. POST bleibt, `build_plan_only_response`, kein Runner-Execute.

## Was ist Phase D.5 (Governance-Router)?

3 C.5-Routen (next-phase, version-governance, source-of-truth) nach `routes_governance.py`. Alle 9 decoupled Routen jetzt in Subroutern.

## Was ist Phase D.6 (Thin Orchestrator)?

Keine Route verschoben. Inventar, Ownership-Matrix, Zielbild (`routes.py` <500 Zeilen, 0 Runner-Imports), D.7+-Reihenfolge, erweiterter Boundary-Guard.

## Was ist Phase D.7 (Evidence-Slice)?

6 weitere plan-only POST-Routen nach `routes_evidence.py` (12 gesamt). `routes.py`: 4671 Zeilen, 99 Runner-Imports. Keine Rescue-/Execute-/Write-Pfade.

## Was ist der Modul-Katalog?

Verbindliches Inventar unter `docs/architecture/MODULE_CATALOG.md` mit Function Ownership Matrix und Do-Not-Duplicate Rules. Cursor muss vor neuer Funktion prüfen, ob ein CANONICAL_MODULE existiert (storage/mount/safety facade, runner stack, deploy sub-router).

## Was ist D.11 (Runtime-Router)?

8 read-only/status POST-Routen in `routes_runtime.py` (Lab-Readiness, Runbook, Validation). `routes.py`: 4324→4120 Zeilen, 89→81 Runner-Imports.

## Was ist E.1 (app.py Router-Slice)?

4 read-only GET-Routen nach `api/routes/health.py` und `version.py` extrahiert (`/health`, `/api/init/status`, `/api/logs/path`, `/api/version`). `app.py`: 17.857→17.779 Zeilen. Evidence: `docs/architecture/APP_ROUTER_SLICE_E1.md`.

## Was ist E.2 (app.py Router-Slice)?

5 read-only GET-Routen nach `api/routes/settings.py` und `status.py` (`/api/settings`, notifications/email, presets/list, debug/routes, user-profile). `app.py`: 17.779→17.699 Zeilen.

## Was ist E.3 (app.py Router-Slice)?

5 read-only GET-Routen: logs/tail, self-update/status, apps, dev-dashboard capability/compact-status. `app.py`: 17.699→17.617 Zeilen.

## Was ist E.4 (app.py Router-Slice)?

5 DCC-Index-GETs nach `dev_dashboard_readonly.py` (modules, evidence-index, manual-command-runs, recent-evidence). Nur `core.dev_dashboard*`. `app.py`: 17.617→17.568 Zeilen.

## Was ist E.5 (Roadmap Router-Slice)?

5 Roadmap-Registry-GETs nach `dev_dashboard_roadmap.py` (areas, milestones, blockers, decisions, next-prompt). Nur `load_roadmap_registry_bundle`. `app.py`: 17.568→17.499 Zeilen.

## Was ist E.6 (Roadmap Next-Prompts)?

2 GET-Routen (`next-prompts`, `export-next-prompt`) in `dev_dashboard_roadmap.py`. `app.py`: 17.499→17.472 Zeilen.

## Was ist E.7 (Router-Slice Kandidaten-Audit)?

Re-Scan aller **187** verbleibenden `@app.*` Routen — **keine Extraktion**. Ergebnis: **3** sichere E.8-Kandidaten. Evidence: `docs/architecture/APP_ROUTER_SLICE_CANDIDATE_AUDIT_E7.md`.

## Was ist E.8 (DCC read-only Router-Slice)?

3 GET-Routen nach `dev_dashboard_readonly.py`: backend-health, notifications/status, notifications/events. Nur `core.dev_dashboard_backend_health` und `core.notification_state`. `app.py`: 17.472→17.425 Zeilen.

## Was ist F.1 (DCC Status Facade)?

Kanonisches Modul `core/dcc_status_facade.py` — read-only Aggregation-Contract für DCC (overview, roadmap, backend-health, notifications, evidence). **Keine Route-Migration** in F.1. Doku: `docs/architecture/DCC_STATUS_FACADE_F1.md`.

## Was ist F.2 (DCC Router-Migration)?

6 Aggregations-GETs in `app.py` delegieren an `dcc_status_facade` (status via Service, roadmap, control-center-summary, project-overview, prompt-findings, cursor-meta-prompt). Keine API-Änderung. Doku: `docs/architecture/DCC_STATUS_ROUTER_MIGRATION_F2.md`.

## Was ist F.3 (DCC Aggregation Audit)?

Reine Analyse ohne Refactoring: verbleibende Direktzugriffe, Ampel-Duplikate, Roadmap-Subrouter-Grenze (`boundary_ok_registry_only`), `ai_prompt_generate_stub` → Facade in F.4, Deploy/Core-Coupling. Doku: `docs/architecture/DCC_AGGREGATION_AUDIT_F3.md`.

## Was ist F.4 (DCC Delegation Cleanup)?

`ai_prompt_generate_stub` und readonly-Router (backend-health, notifications, evidence-index) delegieren an `dcc_status_facade` API-Helper. Keine API-Änderung. Doku: `docs/architecture/DCC_DELEGATION_CLEANUP_F4.md`.

## Was ist G.1 (System Status Facade)?

Kanonisches Modul `core/system_status_facade.py` — read-only Aggregation für Systemampel, Backend-Runtime, Installation, Profil. **Keine Route-Migration** in G.1. Keine Netzwerkdiagnostik. Doku: `docs/architecture/SYSTEM_STATUS_FACADE_G1.md`.

## Was ist G.1b (System Status Router-Migration)?

`GET /api/system/status` in `app.py` delegiert an `build_system_status()`. Keine API-Änderung. Doku: `docs/architecture/SYSTEM_STATUS_ROUTE_MIGRATION_G1B.md`.

## Was ist G.2 (Network Info Facade)?

Kanonisches Modul `core/network_info_facade.py` — read-only Netzwerk-Info, Demo-Fallback, Legacy-Normalisierung. **Keine Route-Migration** in G.2. Doku: `docs/architecture/NETWORK_INFO_FACADE_G2.md`.

## Was ist G.2b (Network Route Migration)?

`GET /api/status` (network-Block) und `GET /api/system/network` delegieren an `network_info_facade`. Keine API-/Response-Änderung. Doku: `docs/architecture/NETWORK_INFO_ROUTE_MIGRATION_G2B.md`.

## Was ist G.3 (Network Core Cleanup)?

`get_system_info` und `webserver_status` delegieren an `network_info_facade`. Legacy `get_network_info`/`_demo_network` bleiben Implementierung hinter Facade-Adapter. Doku: `docs/architecture/NETWORK_INFO_CORE_CLEANUP_G3.md`.

## Was ist H.1 (Frontend Status ViewModel)?

Kanonisches Modul `frontend/src/viewmodels/statusViewModel.ts` — zentrale Status-Normalisierung (StatusKind, Severity, Blocking). **Keine Komponentenmigration** in H.1. Doku: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_H1.md`.

## Was ist H.2 (Frontend Status Utility-Migration)?

`trafficLightModel`, `deployDriftTone` und `toneClass` delegieren an `statusViewModel`. Keine UI-/Farb-Änderung. Doku: `docs/architecture/FRONTEND_STATUS_VIEWMODEL_MIGRATION_H2.md`.

## Was ist H.3 (Frontend Status Component Migration)?

3 kleine DCC-Komponenten delegieren Tone-Mapping an `dashboardLegacyToneFromInput`. Keine UI-Änderung. Doku: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H3.md`.

## Was ist H.4 (Frontend Status Component Migration — zweiter Slice)?

3 weitere kleine Komponenten (`ReadyStableSection`, `StatusCard`, `RiskWarningCard`) delegieren an `isDashboardGreenStatus`, `isGreenDashboardTone`/`dashboardToneFromInput`, `riskWarningTitleKeyForLevel`. Keine UI-Änderung. Doku: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H4.md`.

## Was ist H.5 (Frontend Status Utility Migration)?

3 kleine DCC-Utilities (`governanceMatrix`, `roadmapFilter`, `buildGovernancePrompt`) delegieren Status-Mapping an `statusViewModel`. Keine UI-Änderung. Doku: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5.md`.

## Was ist H.6 (Frontend Status Presentation Migration)?

5 Presentation-/Utility-Dateien delegieren an `statusViewModel` (LampDot, Panda-Ampel, Governance-History, Standalone-Dashboard). Keine UI-Änderung. Doku: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H6.md`.

## Was ist H.7 (Frontend Status — finaler Slice)?

5 Presentation-Libs delegieren an `statusViewModel`. Verbleibend: 10 (Domain + Large-Page). **Kein H.8.** Doku: `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H7.md`.

## Nächster Schritt?

**G.4** — Network Handler Extraction aus `app.py`.

## Weiterlesen

- `docs/architecture/MODULE_CATALOG.md`
- `docs/architecture/FUNCTION_OWNERSHIP_MATRIX.md`
- `docs/architecture/DO_NOT_DUPLICATE_RULES.md`
- `docs/knowledge-base/architecture/CORE_FACADES.md`
- `docs/architecture/STORAGE_DISCOVERY_INVENTORY.md`
- `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4.md`
- `docs/architecture/DEPLOY_RUNNER_REGISTRY.md`
- `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT.md`
- `docs/architecture/DEPLOY_RUNNER_API_FACADE.md`
- `docs/architecture/DEPLOY_RUNNER_RISK_GATE.md`
- `docs/architecture/DEPLOY_ROUTE_TARGET_ARCHITECTURE_D1.md`
- `docs/architecture/DEPLOY_RUNNER_ROUTES_DECOUPLING_C5.md`
