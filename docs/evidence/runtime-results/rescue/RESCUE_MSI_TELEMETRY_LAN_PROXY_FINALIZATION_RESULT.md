# RESCUE MSI Telemetrie LAN-Proxy — Finalisierung

**Datum:** 2026-06-07  
**Workspace-Version:** 1.7.4.6 (vorher 1.7.4.5)  
**Git HEAD vorher:** 6c40e19  
**Runtime-Version API:** 1.7.4.1 (Drift unverändert — `RUNTIME_DEPLOY_DRIFT_1_7_4_5_PENDING`)

## Ergebnis

| Prüfung | Ergebnis |
|---------|----------|
| Eigener Rescue-Telemetrie-LAN-Proxy implementiert | ja |
| Nur Telemetriepfade erreichbar | ja (404 für `/api/version`, `/openapi.json`, `/api/dev-dashboard/status`) |
| LAN-health über Proxy | **HTTP 200** |
| DCC compact `rescue.telemetry_lan_proxy` | ja |
| Frontend-Kachel + Rescue-Toolbox | ja |
| Backend-/Frontend-Tests | grün |
| `target_network_telemetry_validated` | **false** (kein MSI-Boot) |
| `developer_lan_telemetry_proxy_ready` | **true** |
| `windows_inspect_executable` | **false** |

## Proxy

- **Bind:** `192.168.178.140:8001`
- **Upstream:** `http://127.0.0.1:8000`
- **Health-URL:** http://192.168.178.140:8001/api/rescue/telemetry/health
- **Ingest-URL:** http://192.168.178.140:8001/api/rescue/telemetry/v1/ingest
- **PID (Smoke):** siehe `rescue_telemetry_lan_proxy_status_latest.json`
- **Erlaubte Pfade:** GET `/api/rescue/telemetry/health`, POST `/api/rescue/telemetry/v1/ingest`, OPTIONS für beide

## Operator-Befehle

```bash
cd /home/volker/piinstaller
SETUPHELFER_RESCUE_TELEMETRY_BIND=192.168.178.140 ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh
./scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh
./scripts/rescue-live/stop-rescue-telemetry-lan-proxy.sh
```

## Smoke (Developer-Laptop, kein MSI)

```
curl http://127.0.0.1:8000/api/rescue/telemetry/health          → 200 ok
curl http://192.168.178.140:8001/api/rescue/telemetry/health    → 200 ok
curl http://192.168.178.140:8001/api/version                    → 404
curl http://192.168.178.140:8001/openapi.json                   → 404
curl http://192.168.178.140:8001/api/dev-dashboard/status       → 404
status-rescue-telemetry-lan-proxy.sh                            → running=true, lan_health_ok=true
```

## Nächster Operator-Schritt

**Prompt:** `RESCUE_USB_MSI_UEFI_BOOT_NETWORK_TELEMETRY_OPERATOR_RUN`

1. Proxy starten (falls nicht läuft)
2. MSI vom Stick booten (ISO `9ef1b330…`)
3. Im Live-System: `curl` auf health-url
4. Telemetrie-Ingest senden
5. Evidence ingestieren

## Artefakte

- `scripts/rescue-live/rescue_telemetry_lan_proxy.py`
- `scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh`
- `scripts/rescue-live/stop-rescue-telemetry-lan-proxy.sh`
- `scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh`
- `backend/core/rescue_telemetry_lan_proxy.py`
- `docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_status_latest.json`
- `docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_latest.log`
