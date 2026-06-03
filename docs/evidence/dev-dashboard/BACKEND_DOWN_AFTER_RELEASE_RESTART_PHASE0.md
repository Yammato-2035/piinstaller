# Backend Down After Release Restart — Phase 0

**Datum:** 2026-06-03  
**HEAD (Baseline):** `cce563b`  
**Branch:** `main`

## Ist-Zustand (Agent-Baseline, nach Operator-Recovery)

| Prüfpunkt | Wert |
|-----------|------|
| `setuphelfer-backend` | **active** |
| `setuphelfer-backend` failed? | **no** (is-failed: inactive) |
| `setuphelfer` (Web) | **active** |
| Port **8000** listening | **yes** (`127.0.0.1:8000`) |
| Port **3001** listening | **yes** |
| `/api/version` HTTP 200 | **yes** |
| `install_profile` (API) | **release** |
| `profile_gate_status` | **green** |
| `dev_control_enabled` | **false** |

## Ausgangssituation (Operator-Terminal 6, vor Recovery)

Nach DCC-Deploy (`deploy-to-opt.sh`):

- `curl: (7) Failed to connect to 127.0.0.1 port 8000`
- systemd: *The unit file … changed on disk. Run `systemctl daemon-reload`*
- Operator: `sudo systemctl daemon-reload` + `restart setuphelfer-backend` — unmittelbar danach erneut `curl (7)` (Restart-Race / Service noch nicht listening)

## `install-profile.conf`

```ini
[Service]
Environment=SETUPHELFER_INSTALL_PROFILE=release
Environment=SETUPHELFER_DEV_CONTROL_ENABLED=false
Environment=SETUPHELFER_FLEET_SESSIONS_ENABLED=false
Environment=SETUPHELFER_DEV_DIAGNOSTICS_ENABLED=false
Environment=SETUPHELFER_RESCUE_REMOTE_ENABLED=false
```

Drop-Ins geladen u. a.: `90-devserver-local-lab.conf`, `install-profile.conf`, `override.conf`.

## Vorläufige Klassifikation (Ausfallzeitpunkt)

| Kandidat | Bewertung |
|----------|-----------|
| `backend_service_failed` | nein (Service später active) |
| `backend_not_listening` | **ja** (transient nach Deploy/Restart) |
| `backend_import_failure` | nein (`/opt` Import OK) |
| `release_dropin_misconfigured` | nein (release korrekt) |
| `systemd_reload_required` | **ja** (Warnung nach Deploy) |
| `unknown` | nein |

**Primär:** `systemd_reload_required` + transient `backend_not_listening` während Restart.
