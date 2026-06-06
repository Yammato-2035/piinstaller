# Development Server Local Capability Gate — Fix Result

**Version:** 1.7.4.0 → **1.7.4.1**  
**Datum:** 2026-06-06  
**Prompt:** `DEVELOPMENT_SERVER_LOCAL_CAPABILITY_GATE_AND_DCC_STATUS_FIX`

## Problem

Auf dem Developer-Laptop (Release-Profil + `DCC_DEVELOPER_ENABLED` + Token) war das DCC sichtbar, der **Development Server** blieb aber irreführend als **deaktiviert** — obwohl lokal freigegeben.

Ursache: `dev_server_enabled` im Release-Profil ist `false`; Router, Route-Exposure und `load_dev_server_config()` ignorierten die Developer-Capability auf dem Host.

## Fix

| Bereich | Änderung |
|---------|----------|
| `developer_capability.py` | `is_dev_server_host_locally_allowed()` — Host-Gate analog DCC |
| `route_exposure.py` | Dev-Server-Routen + Router-Registrierung bei Host-Capability |
| `devserver_policy.py` | Release + Capability → Defaults `enabled=true`, `mode=local_lab` |
| `devserver/config.py` | Policy auch wenn `capabilities.dev_server_enabled=false` |
| `profile_deploy_manifest.py` | `/api/dev-server` in Capability-Exempt-Prefixes |
| `dev_dashboard_compact_status.py` | Kompaktfeld `dev_server` |
| Frontend | DCC-Kompakt-Kachel Dev-Server |

## Sicherheit (unverändert)

- Fremd-Release ohne Token: DCC + Dev-Server **blockiert**
- Telemetrie `/api/rescue/telemetry/*` **unabhängig** vom DCC
- Dev-Server auf Release nur mit expliziter Host-Capability (`DCC_DEVELOPER_ENABLED` + konfiguriertes Token)
- Env-Override `SETUPHELFER_DEV_SERVER_ENABLED` allein auf Release **ignoriert**

## Operator

Nach Deploy + Backend-Neustart: DCC Kompaktstatus → Dev-Server **local_lab** / enabled; Overview-Header zeigt Dev-Server aktiv.

## Secrets

Keine Secrets in dieser Datei.
