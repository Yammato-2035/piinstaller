# Ports and Profiles — Result

**Datum:** 2026-06-03

## Zusammenfassung

| Aussage | Wert |
|---------|------|
| Zentrale Registry | **yes** — `config/runtime_ports.json` |
| `/api/version` zeigt Ports (Workspace) | **yes** |
| `/api/version` zeigt Ports (`/opt` live) | **nach Deploy** |
| Port 8000 refused = Backend down | **dokumentiert** |
| DCC release-Meldung = Profil, kein Crash | **yes** |
| Healthcheck nutzt Registry | **yes** |
| QEMU Preflight nutzt Registry | **yes** |
| Frontend Port-Hinweis | **yes** |
| QEMU | **no** |

## Verbindliche Ports

- API **8000**, UI/DCC **3001**, nginx **8080** (nicht DCC), QEMU Proxy **8001**, Gast **10.0.2.2:8001**

## Nächster Schritt

1. `sudo ./scripts/deploy-to-opt.sh` (Registry in `/api/version` live)
2. Bei stable Backend + Watchdog: **QEMU Guest Agent Smoke Operator Run**
