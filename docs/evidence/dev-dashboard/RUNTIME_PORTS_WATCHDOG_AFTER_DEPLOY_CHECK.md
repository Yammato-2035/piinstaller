# Runtime Ports — Watchdog After Registry Deploy

**Datum:** 2026-06-03  
**Skript:** `/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh`  
**Exit:** `opt_health_exit=0`

## Watchdog-Snapshot

| Feld | Wert |
|------|------|
| `overall_status` | **ok** |
| `failure_classification` | **none** |
| `api_version_http` | **200** |
| `install_profile` | **release** |
| `profile_gate_status` | **green** |
| `expected_profile_blocks` | **true** |
| `backend_port_8000_listening` | **true** |
| `frontend_port_3001_listening` | **true** |
| `runtime_ports_source` | `/opt/setuphelfer/config/runtime_ports.json` |

Artefakte:

- `runtime_ports_watchdog_oneshot_after_registry_deploy.log`
- `runtime_ports_watchdog_health_after_registry_deploy.json`

## Status

**ok**
