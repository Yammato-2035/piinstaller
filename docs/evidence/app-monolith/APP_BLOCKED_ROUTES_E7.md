# APP Blocked Routes — Phase E.7

**HEAD:** `72a7c93` · Routen, die **nicht** ohne Facade/Core-Refactor extrahiert werden dürfen.

## Pflicht-Blocker (explizit)

| Route | Methode | Blocker | benötigtes Modul/Facade | Empfehlung |
|-------|---------|---------|-------------------------|------------|
| `/api/status` | GET | `_compute_system_status`, subprocess/apt/psutil | **System Status Facade** | Facade zuerst; Route bleibt in `app.py` bis Facade canonical |
| `/api/system/network` | GET | `get_network_info`, `run_command` | **Network Info Facade** | Facade zuerst |
| `/api/dev-dashboard/status` | GET | `build_dashboard_status`, volle DCC-Aggregation | **DCC Status Facade** | Facade + Profil-Gate; höchste DCC-Komplexität |
| `/api/dev-dashboard/roadmap` | GET | `build_dashboard_status` + `dashboard_context` | **DCC Roadmap Facade** oder Core-Refactor Registry ohne Live-Dashboard | E.5/E.6 Subroutes bereits extrahiert; Root-Route blockiert |

## DCC-Aggregation (Core-Refactor)

| Route | Methode | Blocker | benötigtes Modul/Facade | Empfehlung |
|-------|---------|---------|-------------------------|------------|
| `/api/dev-dashboard/control-center-summary` | GET | `build_dashboard_status` + `asyncio.to_thread` | **Dev Dashboard Aggregation Facade** | Nach DCC Status Facade |
| `/api/dev-dashboard/prompt-findings` | GET | `build_dashboard_status` | DCC Aggregation Facade | Cockpit-Findings aus Dashboard-Kontext |
| `/api/dev-dashboard/cursor-meta-prompt` | GET | `build_dashboard_status` | DCC Aggregation Facade | wie prompt-findings |
| `/api/dev-dashboard/project-overview` | GET | DCC/Core-Mix | DCC Aggregation Facade | später |

## Domänen-Blocker (CRITICAL / unsafe)

| Domäne | Beispiel-Routen | Blocker | Empfehlung |
|--------|-----------------|---------|------------|
| Backup | `/api/backup/jobs/*` | Jobs, Evidence-Write, Cancel | `unsafe` — bleibt in Monolith bis Backup-Facade-Phase |
| Restore | `/api/restore/*` | Storage/Safety/Mount | `unsafe` |
| Deploy | `/api/dev-dashboard/deploy/*` | Operator, Runner | `unsafe` |
| Rescue | `/api/dev-dashboard/rescue-*` | ISO/USB/Build-Gates | `keep_until_core_refactor` / `unsafe` |
| Partition Write | `/api/partitions/*` POST | Safety/Mount/Storage | `unsafe` |
| Control Center | `/api/control-center/*` | sudo_store, Hardware-Module | `keep_until_facade` |
| Settings Write | `POST /api/settings*` | Persistenz, SMTP | **Settings Write Facade** vor Router-Slice |

## Guard-Verknüpfung

Neue WARN-only Checks in `scripts/check-module-boundaries.sh` (E.7):

- `app_status_route_requires_system_status_facade`
- `app_network_route_requires_network_facade`
- `app_dcc_status_requires_dcc_status_facade`
- `app_roadmap_route_uses_dashboard_aggregation`
- `app_blocked_route_extraction_attempt` (blockierte Pfade in Router-Slices)

Evidence: [BOUNDARY_WARNINGS_E7.txt](./BOUNDARY_WARNINGS_E7.txt)
