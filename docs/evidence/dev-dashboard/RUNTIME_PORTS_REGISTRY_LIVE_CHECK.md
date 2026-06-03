# Runtime Ports Registry — Live Check

**Datum:** 2026-06-03  
**Quelle:** `runtime_ports_registry_live_api_version_latest.json`  
**Python-Check:** `runtime_ports_live_check_exit=0`

## Einzelprüfungen

| Check | Erwartung | Ergebnis |
|-------|-----------|----------|
| backend_api | port **8000** | **ok** |
| frontend_ui | port **3001** | **ok** |
| nginx_default | port **8080** | **ok** |
| qemu_lab_proxy_host | port **8001** | **ok** |
| qemu_guest_devserver | `http://10.0.2.2:8001` | **ok** |
| DCC URL | `http://127.0.0.1:3001/?window=cockpit` | **ok** |
| api_version URL | `http://127.0.0.1:8000/api/version` | **ok** |
| install_profile | `release` | **ok** |

## Status

**ok**

Alle maschinellen Checks bestanden. Port-Registry ist live in `/api/version`.
