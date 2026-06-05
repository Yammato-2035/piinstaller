# Ports und Profile — SetupHelfer Runtime

**Stand:** 2026-06-03  
**Maschinenlesbar:** `config/runtime_ports.json`  
**Live unter release:** `GET /api/version` → `runtime_ports`, `canonical_urls`, `profile_capabilities`  
**Live-Verifikation (Operator-Deploy `2406e68`):** `docs/evidence/dev-dashboard/RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md`, Readiness `runtime_ports_registry_qemu_readiness_latest.json` (`status=ok`, QEMU nicht ausgeführt)

## Port-Tabelle

| Port | Host | Rolle | URL |
|-----:|------|--------|-----|
| **8000** | 127.0.0.1 | **Backend/API** (FastAPI, alle `/api/*`) | http://127.0.0.1:8000 |
| **3001** | 127.0.0.1 | **Web-UI / DCC-Fenster** | http://127.0.0.1:3001 |
| **8080** | 127.0.0.1 | **nginx/Ubuntu-Default** — **nicht** SetupHelfer-DCC | http://127.0.0.1:8080 |
| **8001** | 127.0.0.1 | **QEMU Lab-Proxy** (Host → Backend) | http://127.0.0.1:8001 |
| **8001** | 10.0.2.2 | **QEMU-Gast Devserver** (slirp) | http://10.0.2.2:8001 |

## Canonical URLs

| Zweck | URL |
|-------|-----|
| DCC | http://127.0.0.1:3001/?window=cockpit |
| Haupt-UI | http://127.0.0.1:3001/ |
| API Version | http://127.0.0.1:8000/api/version |
| Backend Health | http://127.0.0.1:8000/api/dev-dashboard/backend-health |

## Profil-Regeln

### release

| Prüfung | Erwartung |
|---------|-----------|
| `/api/version` | **HTTP 200** |
| `dev_control_enabled` | **false** |
| `/api/dev-dashboard/*` | **404** `PROFILE_ROUTE_BLOCKED` |
| `/api/fleet/*` | **404** `PROFILE_ROUTE_BLOCKED` |
| `/api/rescue-agent/*` | **404** `PROFILE_ROUTE_BLOCKED` |
| DCC UI | Meldung „Development Control nicht verfügbar“ — **erwartet**, kein Crash |
| DCC Live-Akzeptanz | `release` gilt als erwartbarer Sicherheitszustand; funktional grün erst nach `local_lab` live geprüft |

### local_lab

| Prüfung | Erwartung |
|---------|-----------|
| `/api/version` | **HTTP 200** |
| `dev_control_enabled` | **true** |
| `/api/dev-dashboard/status` | **HTTP 200** |
| `/api/dev-dashboard/backend-health` | **HTTP 200** |
| `/api/fleet/sessions` | **HTTP 200** |
| `/api/rescue-agent/sessions` | **HTTP 200** (wenn Router aktiv) |
| DCC Live-Akzeptanz | Cockpit muss Evidence sichtbar machen: `dcc_live_acceptance_latest.json` + `/api/dev-dashboard/*` 200 |

## Typische Fehlinterpretationen

| Symptom | Bedeutung |
|---------|-----------|
| `curl: (7) … port 8000` | **Backend down** oder Restart-Race — **nicht** „falscher DCC-Port“ |
| HTTP **404** `PROFILE_ROUTE_BLOCKED` | **Erwartet** unter release für Dev-Routen |
| `curl -I :8080` zeigt nginx | **Nicht** SetupHelfer — falscher Port |
| DCC „nicht verfügbar“ bei release | **Profil**, kein Portfehler |
| Healthcheck-JSON `install_profile=release` | Snapshot beim Probe — API-Profil vor jedem Call prüfen |

## Siehe auch

- `docs/dev-dashboard/DCC_PORTS_AND_URLS.md`
- `docs/runbooks/DEVELOPER_BACKEND_WATCHDOG_RUNBOOK.md`
