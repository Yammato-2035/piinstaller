# Developer DCC + Telemetrie — Deploy nach /opt (Operator-Handoff)

**Status:** `blocked_awaiting_operator_deploy`  
**Root Cause:** Workspace `efd3966+` enthält `developer_capability.py`, `rescue_telemetry`-Router und korrigiertes Route-Gating; `/opt/setuphelfer/backend` ist älter (Deploy-Drift).

## Ist-Zustand (Live unter `/opt`)

| Prüfung | Live | Workspace (pytest) |
|---------|------|-------------------|
| `developer_capability.py` | fehlt | vorhanden |
| `rescue_telemetry/routers.py` | fehlt | vorhanden |
| `route_exposure.py` (DCC defer) | alt | korrigiert |
| `/api/dev-dashboard/capability-status` | 404 `PROFILE_ROUTE_BLOCKED` | 200 |
| `/api/rescue/telemetry/health` | 404 Not Found | 200 |

**Kein Code-Bug im Workspace** — Middleware auf `/opt` blockiert `/api/dev-dashboard/*` noch über `dev_control_enabled=false`, bevor `capability-status` geprüft wird.

## Operator-Befehle (nur mit expliziter Freigabe)

```bash
cd /home/volker/piinstaller

# 1) Backend + Frontend nach /opt (startet Dienst neu)
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller

# Alternative falls Helper vorhanden:
# sudo ./scripts/setuphelfer-deploy-helper-root.sh /home/volker/piinstaller
```

`deploy-to-opt.sh` führt Backend-Restart ein. **Kein separater Restart nötig**, wenn Deploy erfolgreich.

## Verifikation unmittelbar nach Deploy

```bash
curl -sS http://127.0.0.1:8000/api/version | jq '{project_version,install_profile,backend_runtime_path}'

curl -sS -o /dev/null -w 'capability-status:%{http_code}\n' \
  http://127.0.0.1:8000/api/dev-dashboard/capability-status
# Erwartung: 200 (auch ohne Token)

curl -sS -o /dev/null -w 'telemetry-health:%{http_code}\n' \
  http://127.0.0.1:8000/api/rescue/telemetry/health
# Erwartung: 200 (nicht 404, nicht PROFILE_ROUTE_BLOCKED)

curl -sS http://127.0.0.1:8000/api/dev-dashboard/capability-status | jq .
# Erwartung: reason=DEVELOPER_CAPABILITY_REQUIRED oder PROFILE_ROUTE_BLOCKED (ohne Token ok)
# Kein Secret in Response
```

## Frontend (DCC UI :3001)

Deploy-Skript baut Frontend mit. Nach Deploy:

```bash
curl -sS -o /dev/null -w 'frontend_3001:%{http_code}\n' http://127.0.0.1:3001/
```

DCC muss Kompaktstatus + Telemetrie-Health anzeigen (nicht leer bei blockiertem DCC).

## Nächste Schritte nach Deploy

1. `docs/evidence/dev-dashboard/DEVELOPER_DCC_CAPABILITY_LOCAL_CONFIG_OPERATOR_HANDOFF.md` — Token + `developer.env`
2. Smoke: `DEVELOPER_DCC_AND_TELEMETRY_OPERATOR_SMOKE_RESULT.md` aktualisieren
3. Erst dann: `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT`

## Verboten im Agent

- Kein `sudo ./scripts/deploy-to-opt.sh` ohne Operator-Freigabe
- Kein Token ins Repo/Evidence
