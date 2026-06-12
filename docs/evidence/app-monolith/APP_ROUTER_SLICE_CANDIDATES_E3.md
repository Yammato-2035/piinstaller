# APP Router Slice — Kandidaten E.3

**HEAD (Baseline):** `b667785` (nach E.2)

## Ausgewählte E.3-Routen

| Route | Funktion | Domain | Risiko | E.3 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /api/logs/tail` | `logs_tail` | diagnostics | low | **ja** | Log-Datei read_text, kein subprocess |
| `GET /api/self-update/status` | `self_update_status` | runtime | low | **ja** | version.json/Pfad-Vergleich, kein subprocess |
| `GET /api/apps` | `get_apps` | frontend_support | low | **ja** | Statischer `APPS_CATALOG` |
| `GET /api/dev-dashboard/capability-status` | `dev_dashboard_capability_status` | dev_dashboard | low | **ja** | `core.developer_capability`, kein Aggregat |
| `GET /api/dev-dashboard/compact-status` | `dev_dashboard_compact_status` | dev_dashboard | low | **ja** | `core.dev_dashboard_compact_status`, kompakt |

## Explizit ausgeschlossen

| Route | Funktion | Domain | Risiko | E.3 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /api/status` | `get_status` | health | medium | nein | `get_network_info()` subprocess |
| `GET /api/system/network` | `get_system_network` | runtime | medium | nein | subprocess |
| `GET /api/dev-dashboard/status` | `dev_dashboard_status` | dev_dashboard | high | nein | Volle DCC-Aggregation |
| `GET /api/dev-dashboard/control-center-summary` | … | dev_dashboard | medium | nein | `asyncio.to_thread` + Dashboard-Build |
| `GET /api/apps/{app_id}/status` | `get_app_status` | frontend_support | medium | nein | `run_command`/`docker` |
| `GET /api/security/status` | `security_status` | security | medium | nein | `get_running_services` Low-Level |
| Backup/Restore/Deploy/Rescue | diverse | diverse | high | nein | Domänen-Ausschluss |

## Module-Reuse

- `core.developer_capability`, `core.dev_dashboard_compact_status`, `core.install_profile`
- `core.install_paths.get_backend_runtime_dir`
- Lazy-Imports aus `app` für `LOG_PATH`, `APPS_CATALOG`, `OPT_INSTALL_DIR`
