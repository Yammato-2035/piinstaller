# APP Route Re-Scan — Phase E.7

**Baseline HEAD:** `72a7c93` (nach E.6)  
**Quelle:** `backend/app.py` (statischer Scan, Handler-Body ±120 Zeilen)  
**Gesamt:** 187 verbleibende `@app.*` Routen · 17.472 Zeilen

## Kontext

E.1–E.6 extrahierten **26** read-only GET-Routen in acht Router-Module. E.7 ist **reine Kandidaten-Analyse** — keine Route verschoben.

## Verteilung

| Kategorie | Anzahl |
|-----------|--------|
| **GET** | 94 |
| **POST** | 87 |
| **PUT** | 4 |
| **DELETE** | 2 |

| `recommended_action` | Anzahl |
|--------------------|--------|
| `unsafe` | 109 |
| `keep_until_facade` | 63 |
| `keep_until_core_refactor` | 8 |
| `already_extracted` | 4 |
| `extract_next` | 3 |

| Domäne | Anzahl |
|--------|--------|
| runtime | 74 |
| backup | 33 |
| frontend_support | 23 |
| unknown | 21 |
| dev_dashboard | 14 |
| rescue | 9 |
| security | 8 |
| deploy | 4 |
| health | 1 |

## E.8-Kandidaten (`extract_next`)

| Zeile | Pfad | Funktion | Core-Modul |
|-------|------|----------|------------|
| 4061 | `GET /api/dev-dashboard/backend-health` | `dev_dashboard_backend_health` | `core.dev_dashboard_backend_health`, `core.dev_dashboard_status_service` |
| 4258 | `GET /api/dev-dashboard/notifications/status` | `dev_dashboard_notifications_status` | `core.notification_state` |
| 4270 | `GET /api/dev-dashboard/notifications/events` | `dev_dashboard_notifications_events` | `core.notification_state` |

## Explizit blockiert (Facade/Core vor Extraktion)

| Pfad | Grund |
|------|-------|
| `GET /api/status` | `_compute_system_status` / subprocess |
| `GET /api/system/network` | `get_network_info` / subprocess |
| `GET /api/dev-dashboard/status` | volle DCC-Aggregation |
| `GET /api/dev-dashboard/roadmap` | `build_dashboard_status` + Registry |
| `GET /api/dev-dashboard/control-center-summary` | DCC-Aggregation + Summary |
| `GET /api/dev-dashboard/prompt-findings` | `build_dashboard_status` |
| `GET /api/dev-dashboard/cursor-meta-prompt` | `build_dashboard_status` |
| Rescue/Deploy/Backup/Restore/Partition-Write | CRITICAL — nicht extrahierbar |

## CSV

Vollständiges Inventar: [APP_ROUTE_RESCAN_E7.csv](./APP_ROUTE_RESCAN_E7.csv)

Pflichtfelder: line, method, path, function_name, domain, risk, uses_subprocess, uses_systemctl, uses_storage, uses_safety, uses_mount, uses_dcc_aggregation, uses_file_scan, recommended_action.
