# Function Ownership Matrix

**Stand:** Modul-Katalog-Phase · Verbindliche Zuordnung von Fähigkeiten zu Eigentümermodulen.

| Funktion / Fähigkeit | Eigentümermodul | Status | Nutzer | Nicht erneut bauen |
|---|---|---|---|---|
| Storage Discovery | `storage_facade` | CANONICAL | app, backup, partitions, inspect | Ja |
| blkid / UUID-Erkennung | `storage_facade` | CANONICAL | storage_facade, safe_device (legacy allow) | Ja |
| lsblk / Device Tree | `storage_facade` | CANONICAL | storage_facade, storage_detection (partial) | Ja |
| findmnt / Mount-Erkennung | `mount_facade` | CANONICAL | mount_facade, backup_target_auto_prepare | Ja |
| Storage Target Classification | `storage_facade` | CANONICAL | safety_facade, inspect | Ja |
| Write Target Validation | `safety_facade` | CANONICAL | backup_engine, restore_engine, preflight | Ja |
| Safe Device Check | `safe_device` + `safety_facade` | PARTIAL | app, backup modules | Facade bevorzugen |
| Write Guard | `safety/write_guard.py` | PARTIAL | legacy callers | safety_facade bevorzugen |
| Restore Target Validation | `safety_facade` | CANONICAL | restore_engine, rescue runners | Ja |
| Partition Target Validation | `safety_facade` | CANONICAL | partition_storage_facade, partitions UI | Ja |
| Readonly Mount Plan | `mount_facade` | CANONICAL | rescue readonly orchestrator | Ja |
| Source-vs-Target Validation | `mount_facade` | CANONICAL | rescue, restore preview | Ja |
| Runner Metadata | `runner_registry` | CANONICAL | facade, risk_gate, contract | Ja |
| Runner Registry Scan | `runner_registry` | CANONICAL | CI boundary, tests | Ja |
| Runner Result Contract | `runner_result_contract` | CANONICAL | all runners (output shape) | Ja |
| Runner Risk Gate | `runner_risk_gate` | CANONICAL | runner_api_facade | Ja |
| Runner Catalog API | `runner_api_facade` | CANONICAL | routes_registry | Ja |
| Deploy Registry Routes | `routes_registry` | CANONICAL | routes.py orchestrator | Ja |
| Deploy Risk Gate Routes | `routes_risk_gate` | CANONICAL | routes.py orchestrator | Ja |
| Evidence Plan Routes | `routes_evidence` | CANONICAL | routes.py orchestrator | Ja |
| Governance Plan Routes | `routes_governance` | CANONICAL | routes.py orchestrator | Ja |
| Diagnostics Plan Routes | `routes_diagnostics` | CANONICAL | routes.py orchestrator | Ja |
| Versioning Plan Routes | `routes_versioning` | CANONICAL | routes.py orchestrator | Ja |
| Runtime Readonly Routes | `routes_runtime` | CANONICAL | routes.py orchestrator | Ja |
| Health Liveness API | `api/routes/health.py` | CANONICAL | app (include_router) | Ja |
| Version Gate API | `api/routes/version.py` | CANONICAL | app (include_router) | Ja |
| Settings Read API | `api/routes/settings.py` | CANONICAL | app (include_router) | Ja |
| Status/Metadata Read API | `api/routes/status.py` | CANONICAL | app (include_router) | Ja |
| DCC Capability Gate API | `api/routes/capabilities.py` | CANONICAL | app (include_router) | Ja |
| App Catalog API | `api/routes/catalog.py` | CANONICAL | app (include_router) | Ja |
| DCC Readonly Index API | `api/routes/dev_dashboard_readonly.py` | CANONICAL | app (include_router) | Ja (8 GET nach E.8) |
| DCC Roadmap Registry API | `api/routes/dev_dashboard_roadmap.py` | CANONICAL | app (include_router) | Ja |
| System Status (Ampel) | `app.py` `_compute_system_status` | PARTIAL | `/api/status`, `/api/system/status` | **CANDIDATE:** System Status Facade (E.7) |
| Network Info | `app.py` `get_network_info` | PARTIAL | `/api/system/network` | **CANDIDATE:** Network Info Facade (E.7) |
| DCC Full Status | `core.dev_dashboard` via app route | PARTIAL | `/api/dev-dashboard/status` | **CANDIDATE:** DCC Status Facade (E.7) |
| DCC Backend Health Snapshot | `core.dev_dashboard_backend_health` | CANONICAL | `dev_dashboard_readonly` router (E.8) | Ja |
| Notification State Read | `core.notification_state` | CANONICAL | `dev_dashboard_readonly` router (E.8) | Ja |
| Deploy Execute/Rescue Routes | `routes.py` | LEGACY | app | Bis D.15 Execute-Gate |
| Status / Ampel Mapping | — (verteilt) | PARTIAL | frontend, DCC | PLANNED: zentrales ViewModel |
| DCC Aggregation | `dev-dashboard` routes in app | PARTIAL | DevelopmentDashboard.tsx | Keine Parallel-Aggregation |
| Frontend API Clients | `frontend/src/lib/*` | PARTIAL | pages, rescue UI | Wiederverwenden |
| i18n Namespaces | `frontend/src/**/i18n` | PARTIAL | rescue, main UI | Namespace-Konzept |
| Notification Events | — | MISSING | — | D.9: keine Deploy-Routen |
| Backup Job State | `backup_engine` + API | PARTIAL | app routes | Kein zweites State-Modell |
| Restore Preview State | `restore_engine` + API | PARTIAL | app routes | Facades für Safety |

**Status-Legende:** CANONICAL = Source of Truth · PARTIAL = Migration läuft · LEGACY = abbauen · PLANNED = dokumentiert · MISSING = nicht vorhanden
