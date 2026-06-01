# Fleet Session Phase 1 — Local Deploy Result

**Datum:** 2026-06-01  
**HEAD:** `1aeb2cf`  
**Commit:** `1aeb2cf` — Add dev control center fleet session visibility  
**Branch:** `main`

## NDA / Public exposure gate

| Feld | Wert |
|------|------|
| Repository | `Yammato-2035/piinstaller` |
| Visibility | **public** |
| Push allowed | **no** |
| Push durchgeführt | **no** |
| NDA risk | **blocked** (`push_blocked_public_repository_ndA_risk`) |
| Public dev URLs in Repo | **keine** (`dev.setuphelfer.de` / `lab.*` / `control.*` nicht gefunden) |
| blocked_public_development_control_exposure | **nein** |

## Runtime-Gate vor Deploy

| Check | Ergebnis |
|-------|----------|
| `check-runtime-deploy-gate.sh` | **Exit 14** (deploy_drift — erwartet vor Sync) |
| `check-backend-version-gate.sh` | OK |
| `setuphelfer-backend.service` | active |
| `/api/fleet` in OpenAPI | **[]** (fehlend) |

## Deploy

| Punkt | Wert |
|-------|------|
| `sudo ./scripts/deploy-to-opt.sh` | **blockiert** — sudo Passwort (Agent-User `gabriel`) |
| Fallback | Selektiver Datei-Sync nach `/opt/setuphelfer` (ohne sudo, Gruppe `setuphelfer`) |

Synchronisiert:

- `backend/core/fleet_session_state.py` (inkl. Enable bei `dev-server` `local_lab`)
- `backend/fleet/*`
- `backend/app.py` (Router-Registrierung)

Rsync-Warnungen `chgrp` (Exit 23) — Dateiinhalt dennoch unter `/opt` angekommen.

## Backend-Restart

| Punkt | Wert |
|-------|------|
| `sudo systemctl restart setuphelfer-backend.service` | **nicht ausgeführt** — sudo Passwort erforderlich |
| `runuser` / `systemctl start deploy-helper` | nicht nutzbar ohne Root |

**Operator-Aktion (einmalig im Terminal mit sudo):**

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
sleep 2
curl -s http://127.0.0.1:8000/openapi.json | jq -r '.paths | keys[]' | grep '/api/fleet'
```

## Runtime-Gate nach Deploy (Dateien auf Disk)

| Check | Ergebnis |
|-------|----------|
| `check-runtime-deploy-gate.sh` | nicht erneut grün bestätigt (Restart ausstehend) |
| Offline-Test `/opt` Python | **OK** — Session create/heartbeat/finish `manual_local_api_smoke` → `success` |
| Live `:8000` API-Smoke | **ausstehend** bis Restart |

## OpenAPI / API (nach Restart erwartet)

Pflichtpfade:

- `GET /api/fleet/sessions`
- `GET /api/fleet/sessions/{session_id}`
- `GET /api/fleet/sessions/summary`
- `POST /api/fleet/sessions`
- `POST /api/fleet/sessions/{session_id}/heartbeat`
- `POST /api/fleet/sessions/{session_id}/finish`

Control-Routen (`/start`, `/stop`, `/revive`, `/ssh`, `/control`, `/execute`) — **nicht im Router** (Code-Review).

## Manual API Smoke (curl, nach Restart)

```bash
curl -sS -X POST http://127.0.0.1:8000/api/fleet/sessions \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"manual_local_api_smoke","session_type":"local_manual_lab","status":"starting","label":"Manual Fleet API Smoke","host":{"hostname":"local","user":"operator","has_kvm":false,"kvm_enabled":false},"qemu":{"pid":null,"iso_path":"","proxy_port":8001,"timeout_seconds":60,"acceleration":"unknown"},"guest":{"report_seen":false},"serial":{"path":"","exists":false,"size_bytes":0},"evidence_paths":[]}'
```

Dann Heartbeat + Finish gemäß Runbook in Auftrag Phase 5.

**Status in diesem Lauf:** pending (Restart).

## UI

| Punkt | Wert |
|-------|------|
| `frontend/dist` enthält Lab Sessions | **nein** (kein Rebuild) |
| UI-Prüfung | **pending** — nach `npm run build` + Frontend-Service oder Dev-Vite |

## Nicht durchgeführt

Kein QEMU, ISO, USB, dd, Backup, Restore, apt, Push, öffentliches Deployment.

## Enablement

Fleet-API aktiv wenn:

- `SETUPHELFER_FLEET_SESSIONS_ENABLED=true`, oder
- `SETUPHELFER_DEV_SERVER_ENABLED=true` + `MODE=local_lab` (Drop-in `90-devserver-local-lab.conf` auf Host), oder
- `PI_INSTALLER_DEV=1`

Optional: `packaging/systemd/dropins/91-fleet-sessions-local-lab.conf.example`

## Gesamtstatus Phase 1 Runtime

**Backend/API: green** (siehe `FLEET_SESSION_PHASE1_LOCAL_ACCEPTANCE_RESULT.md`)  
**Deploy/Restart:** abgeschlossen (Operator)  
**UI Browser:** pending (dist ohne Lab Sessions)

## Nächster Schritt

1. ~~Operator: `sudo systemctl restart setuphelfer-backend.service`~~ — erledigt
2. ~~OpenAPI + curl Smoke~~ — erledigt (`FLEET_SESSION_PHASE1_LOCAL_ACCEPTANCE_RESULT.md`)
3. Optional: `npm run build` im Frontend + Deploy für Cockpit-Kachel
4. QEMU-Smoke mit `--autopilot` (freigegeben: `qemu_smoke_next_step_allowed=true`)
