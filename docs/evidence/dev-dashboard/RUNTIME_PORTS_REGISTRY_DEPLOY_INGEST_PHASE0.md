# Runtime Ports Registry — Deploy Ingest Phase 0

**Datum:** 2026-06-03  
**Auftrag:** INGEST LIVE RUNTIME PORT REGISTRY (Operator-Deploy bereits ausgeführt)  
**HEAD:** `2406e68`  
**Branch:** `main`

## Runtime-Profil

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `profile_gate_status` | `green` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |

## Gates

| Gate | Ergebnis |
|------|----------|
| `check-runtime-profile-deploy-gate.sh` | **OK** (profile-aware) |
| `check-runtime-deploy-gate.sh` | Legacy exit 20 (dev-dashboard 404 unter release — erwartet) |

## Dienst & Ports

| Prüfung | Ergebnis |
|---------|----------|
| `setuphelfer-backend.service` | **active** |
| `setuphelfer.service` | **active** |
| Port **8000** listening | **yes** (`127.0.0.1:8000`) |
| Port **3001** listening | **yes** (`127.0.0.1:3001`) |
| Port **8080** listening | **yes** (nginx, nicht DCC) |
| Port **8001** listening | **no** (QEMU-Proxy nur bei Lab-Smoke) |

## `/api/version` Live

| Feld | Vorhanden |
|------|-----------|
| `runtime_ports` | **yes** |
| `canonical_urls` | **yes** |
| `port_registry_source` | `/opt/setuphelfer/config/runtime_ports.json` |

Artefakt: `runtime_ports_registry_live_api_version_latest.json`

## Nicht-Ziele (eingehalten)

- Kein ISO-Build
- Kein QEMU
- Kein USB/dd
- Kein Backup / Restore
- Kein Deploy in diesem Lauf
- Kein Profilwechsel
