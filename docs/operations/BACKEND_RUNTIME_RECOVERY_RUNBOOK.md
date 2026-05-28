# BACKEND_RUNTIME_RECOVERY_RUNBOOK

## Zweck

Operator-Runbook fuer Backend-Hang (`service active`, `port 8000 LISTEN`, HTTP timeout).

## Diagnose

```bash
systemctl is-active setuphelfer-backend.service
systemctl status setuphelfer-backend.service --no-pager
ss -ltnp | grep ':8000' || true
curl -sS -m 5 http://127.0.0.1:8000/health || true
curl -sS -m 5 http://127.0.0.1:8000/api/version || true
./scripts/check-runtime-deploy-gate.sh || true
echo "Gate exit: $?"
```

### Gate-Exit-Codes (Auszug)

| Exit | Code |
|------|------|
| 17 | `backend_hanging_active_port_but_http_timeout` (`/health` timeout, Port offen) |
| 18 | `backend_version_endpoint_timeout` (`/health` OK, `/api/version` timeout) |
| 14 | deploy_drift — Backend-Dateien deployen (kein Hang) |

## Hang-Intervention (Operator, privilegiert)

```bash
sudo journalctl -u setuphelfer-backend.service -n 200 --no-pager
sudo systemctl restart setuphelfer-backend.service
curl -sS -m 5 http://127.0.0.1:8000/health
curl -sS -m 5 http://127.0.0.1:8000/api/version
./scripts/check-runtime-deploy-gate.sh
```

## Bewertung

- Wenn `/health` + `/api/version` 200 und Gate Exit 0: Runtime wieder verfuegbar.
- Bei weiterem Timeout: als `backend_hanging` klassifizieren und Watchdog-MVP priorisieren.

## Optionaler Healthcheck-Timer (nicht standardmaessig aktiv)

- Skript: `scripts/healthcheck/setuphelfer-backend-healthcheck.sh`
- Beispiel-Units: `packaging/systemd/setuphelfer-backend-healthcheck.{service,timer}.example`
- Default: `ENABLE_RESTART=0` (nur melden). Restart nur mit Operator-Freigabe und `ENABLE_RESTART=1`.
- **Nicht** automatisch `systemctl enable` ohne Freigabe.

## Deploy nach Code-Hardening (Watchdog/Liveness)

```bash
cd /home/volker/piinstaller
sudo systemctl start setuphelfer-deploy-helper.service
journalctl -u setuphelfer-deploy-helper.service -n 120 --no-pager
./scripts/check-runtime-deploy-gate.sh
```

Agent ohne interaktives sudo: Handoff `docs/evidence/dev-dashboard/DEPLOY_SYNC_AFTER_WATCHDOG_OPERATOR_HANDOFF.md`.

## Wichtig

- Deploy nur ueber Deploy-Helper, kein manuelles `cp` nach `/opt`.
- Rescue/Backup/Restore bleiben blockiert, bis Gate wieder gruen ist.
