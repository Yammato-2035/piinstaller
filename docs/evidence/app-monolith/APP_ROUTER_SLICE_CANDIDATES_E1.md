# APP Router Slice — Kandidaten E.1

**HEAD (Baseline):** `5a8a54c`  
**Kriterien:** GET, read-only, keine Schreiboperation, kein Backup/Restore/Deploy/Rescue, keine Storage-/Safety-Subprocess-Duplikate.

## Ausgewählte E.1-Routen

| Route | Funktion | Domain | Risiko | E.1 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /health` | `health_check` | health | low | **ja** | `core.liveness.build_health_payload`, kein subprocess |
| `GET /api/init/status` | `init_status` | frontend_support | low | **ja** | Nur CONFIG_STATE/config_path, read-only |
| `GET /api/logs/path` | `logs_path` | diagnostics | low | **ja** | Pfad-Metadaten, kein tail/subprocess |
| `GET /api/version` | `get_version` | version | low | **ja** | Read-only Versions-Gate; `request.app.routes` statt globalem `app` |

## Explizit ausgeschlossen (Auszug)

| Route | Funktion | Domain | Risiko | E.1 geeignet | Grund |
|-------|----------|--------|--------|--------------|-------|
| `GET /api/system/status` | `system_status` | runtime | medium | nein | `asyncio.to_thread`, apt/psutil |
| `GET /api/status` | `get_status` | health | medium | später | Netzwerk/Demo-Mode |
| `GET /api/system/paths` | `get_system_paths` | runtime | medium | nein | `_root_mount_device()` |
| `GET /api/dev-dashboard/*` | diverse | dev_dashboard | high | nein | DCC-Aggregation |
| `POST /api/*` | diverse | diverse | high | nein | Schreiboperationen |
| Backup/Restore/Partition-Write | diverse | backup/restore/partitions | high | nein | Safety/Storage-Pfade |

## Module-Reuse

- **Health:** `core.liveness`, `core.install_paths`
- **Version:** `core.liveness`, `runtime_governance.service`, `app_bootstrap.version_router_diagnostics`
- **Keine** neuen Storage-/Safety-/Mount-Facades
