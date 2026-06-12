# DCC Status / Ampel Duplicate Analysis — Phase F.3

**HEAD:** `8bb910c`

## Duplikat-Cluster

| Datei | Status-/Ampel-Logik | Domäne | Duplikat-Risiko | Ziel-Owner |
|-------|-------------------|--------|-----------------|------------|
| `core/dcc_status_facade.py` | `build_section_status`, `_LEGACY_STATUS_MAP` | DCC Facade | **niedrig** (kanonisch) | `dcc_status_facade` |
| `core/dev_dashboard_cockpit.py` | `_normalize_ampel` (green/yellow/red) | Cockpit/Findings | **mittel** | `dcc_status_facade` (Mapping) + Cockpit (Daten) |
| `core/dev_dashboard_roadmap.py` | `ALLOWED_STATUS_VALUES`, `_summary_status` | Roadmap Registry | **niedrig** (Domäne) | `allowed_local` (Roadmap-native) |
| `core/project_overview_dashboard_state.py` | `_normalize_status` (green/yellow/red/gray) | Project Overview | **mittel** | `dcc_status_facade` für HTTP; lokal für Overview |
| `core/notification_state.py` | `_summary_status` (green/yellow/gray) | Notifications | **niedrig** | `allowed_local` (Notification-native) |
| `core/dev_dashboard_backend_health.py` | ok/warning/blocked/unknown | Backend Health | **niedrig** | `allowed_local` |
| `core/deploy_job_state.py` | `_runtime_gate_status` (green/yellow/red) | Deploy Runtime Gate | **hoch** | `system_status_facade_future` |
| `app.py` | `_compute_system_status` Ampeln | System `/api/status` | **hoch** | `system_status_facade_future` |
| `frontend/trafficLight/trafficLightModel.ts` | UI Traffic-Light Mapping | Frontend | **hoch** | `frontend_viewmodel_future` |
| `frontend/.../ControlCenterOverviewHeader.tsx` | `trafficFromGate` | DCC UI | **mittel** | `frontend_viewmodel_future` |

## Bewertung

- **Kanonisches Facade-Vokabular** (`ok`, `warning`, `degraded`, `blocked`, `unavailable`, `unknown`) existiert nur in `dcc_status_facade`.
- **Roadmap/Notification** behalten native Ampel-Farben in Payload — bewusst, dokumentiert in F.1.
- **Höchstes Risiko:** parallele green/yellow/red-Mappings in Cockpit, Project Overview, Deploy Gate, Frontend — keine neue Logik in F.3; Konsolidierung über ViewModel/Facades in F.4+.

## Empfehlung

Keine neue Status-Taxonomie in F.3. Nächste Schritte: System Status Facade, Frontend ViewModel, Deploy-Gate über Facade-Hook.
