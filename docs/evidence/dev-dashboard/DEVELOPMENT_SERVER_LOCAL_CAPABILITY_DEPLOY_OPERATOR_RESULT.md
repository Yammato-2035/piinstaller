# DEVELOPMENT_SERVER_LOCAL_CAPABILITY_DEPLOY_OPERATOR_RESULT

**Datum:** 2026-06-06  
**Prompt:** `DEVELOPMENT_SERVER_LOCAL_CAPABILITY_DEPLOY_OPERATOR_RUN`  
**HEAD:** `345187b` (unverändert) · **Commit/Push:** nein

## Ergebnis

**Teilweise Deploy** — kritische Dateien nach `/opt/setuphelfer` synchronisiert, **`verify_deploy_to_opt --phase all` OK**, aber **laufender Backend-Prozess nicht neu gestartet** (Agent-`sudo` blockiert). Dev-Server-Routen im **alten** Uvicorn-Prozess weiter nicht aktiv.

## Phase 0 — Preflight

| Prüfung | Ergebnis |
|---------|----------|
| HEAD | `345187b` |
| Workspace-Version | `1.7.4.1` |
| Live vor Sync | `1.7.4.0` (Drift erwartet) |
| `check_version_consistency` | ok |

## Phase 1 — Deploy

| Aktion | Ergebnis |
|--------|----------|
| `sudo ./scripts/deploy-to-opt.sh` | **blockiert** (kein sudo-Passwort in Agent-Session) |
| Manueller Sync (cp) | Backend-Gate-Dateien + Version + Frontend-Quellen nach `/opt` |
| `verify_deploy post-rsync` | **ok=True** |
| `verify_deploy --phase all` | **ok=True** (Dateien auf Disk) |

## Phase 2 — Version / Gate

| Feld | Live API |
|------|----------|
| `project_version` | **1.7.4.1** (aus aktualisierter `config/version.json`) |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `check-backend-version-gate.sh` | **OK** |

**Hinweis:** API-Version spiegelt Datei auf Disk; **Python-Code im Prozess PID ~1062771 ist noch alt** (kein Reload).

## Phase 3–6 — Smoke (Live-Prozess)

### Ohne Token

- `/api/dev-dashboard/status` → **404** ✓  
- `/api/dev-dashboard/capability-status` → **200**, `DEVELOPER_CAPABILITY_REQUIRED` ✓  
- `/api/rescue/telemetry/health` → **200** ✓  

### Mit Token (Länge 64, Wert nicht geloggt)

- Capability: `developer_capability_valid=true`, `dcc_visible=true` ✓  
- DCC Status: **HTTP 200** ✓  
- OpenAPI `/api/dev-server/*`: **0 Routen** ✗  
- `/api/dev-server/health`: **404** `PROFILE_ROUTE_BLOCKED` ✗  
- Compact: `dev_server`-Objekt **vorhanden**, aber `enabled=false`, `host_locally_allowed=false` ✗  
- Telemetrie: `health_ok=true` ✓  

### Frischer Python-Prozess (Disk-Stand, nicht Uvicorn)

```text
dev_server_locally_allowed=True
load_dev_server_config: enabled=True mode=local_lab
developer_capability.py SHA256 = Workspace
```

→ Fix auf Disk **korrekt**; **Service-Neustart fehlt**.

## Fehlerklassifikation

| Code | zutreffend |
|------|------------|
| `DEPLOY_NOT_APPLIED_OR_OLD_RUNTIME_PROCESS` | **ja** |
| `DEVSERVER_ROUTER_NOT_REGISTERED_AFTER_DEPLOY` | **ja** |
| `DEVSERVER_CAPABILITY_ROUTE_GATE_FAILURE` | nein (Code auf Disk ok) |
| `DEVSERVER_COMPACT_STATUS_MISSING_FIELD` | nein (Feld da, Werte stale) |

## Operator — verbleibender Schritt

Im **Operator-Terminal** (nicht Agent):

```bash
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
sleep 3
./scripts/check-backend-version-gate.sh

TOKEN="$(sudo cat /etc/setuphelfer/dcc_developer.token)"
curl -sS -H "X-Setuphelfer-Developer-Token: $TOKEN" \
  http://127.0.0.1:8000/openapi.json | jq '[.paths | keys[] | select(test("dev-server"))] | length'

curl -sS -H "X-Setuphelfer-Developer-Token: $TOKEN" \
  http://127.0.0.1:8000/api/dev-server/health | jq '{enabled,mode,storage_ok}'

curl -sS -H "X-Setuphelfer-Developer-Token: $TOKEN" \
  http://127.0.0.1:8000/api/dev-dashboard/compact-status | jq '.dev_server'
```

Erwartung nach Restart: OpenAPI >0 Dev-Server-Routen, `enabled=true`, `mode=local_lab`.

Optional vollständiger Deploy später: `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller`

## Erfolgskriterien

**Nicht vollständig grün** — Restart ausstehend.

## Next Prompt

**`DEVELOPMENT_SERVER_LOCAL_CAPABILITY_BACKEND_RESTART_OPERATOR_RUN`**

Falls Restart nicht hilft: **`DEVELOPMENT_SERVER_LOCAL_CAPABILITY_ROUTE_GATE_TRIAGE`**

Parallel Rescue unverändert: **`RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`**

## Nicht ausgeführt

- Vollständiges `deploy-to-opt.sh` (sudo)
- `systemctl restart` (sudo)
- Push, Commit, ISO, USB, Backup/Restore, apt

## Secrets

Keine Token-Werte in dieser Datei.
