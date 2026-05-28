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
```

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

## Wichtig

- Dieses Runbook fuehrt keinen Deploy aus.
- Rescue/Backup/Restore bleiben blockiert, bis Gate wieder gruen ist.
