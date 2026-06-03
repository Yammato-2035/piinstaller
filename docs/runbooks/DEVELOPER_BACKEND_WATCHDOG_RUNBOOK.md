# Runbook — Developer Backend Watchdog

**Zielgruppe:** Operator / Entwickler (nicht Produktions-Autopilot)

## Deploy nach `/opt` (Operator, sudo)

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
test -f /opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh
/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh
```

Evidence: `docs/evidence/dev-dashboard/DEVELOPER_BACKEND_WATCHDOG_DEPLOY_LIVE_RESULT.md`

## Einmaliger Healthcheck (ohne sudo)

```bash
cd /home/volker/piinstaller
./scripts/dev-dashboard/check-backend-health.sh
cat docs/evidence/dev-dashboard/backend_health_latest.json | python3 -m json.tool
```

Exit-Codes: `0` ok, `1` warning, `2` blocked.

## Timer installieren (optional, nur bei Bedarf)

**Nicht** automatisch aktivieren. Pfade und User im Service-Beispiel anpassen.

```bash
sudo install -m 0644 packaging/systemd/setuphelfer-dev-healthcheck.service.example \
  /etc/systemd/system/setuphelfer-dev-healthcheck.service
sudo install -m 0644 packaging/systemd/setuphelfer-dev-healthcheck.timer.example \
  /etc/systemd/system/setuphelfer-dev-healthcheck.timer
# ExecStart/WorkingDirectory/User im Service anpassen
sudo systemctl daemon-reload
sudo systemctl enable --now setuphelfer-dev-healthcheck.timer
```

## Timer deaktivieren

```bash
sudo systemctl disable --now setuphelfer-dev-healthcheck.timer
```

## Logs / Evidence

- Latest: `docs/evidence/dev-dashboard/backend_health_latest.json`
- Historie: `docs/evidence/dev-dashboard/backend_health_history.jsonl`
- Timer-Logs: `journalctl -u setuphelfer-dev-healthcheck.service -n 50`

## Keine automatische Recovery

Der Watchdog **startet keine Services neu**. Bei `overall_status=blocked`:

```bash
systemctl status setuphelfer-backend.service
journalctl -u setuphelfer-backend.service -n 200 --no-pager
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, dev_control_enabled}'
```

Nach Unit-/Drop-in-Änderungen immer **`daemon-reload` vor `restart`**.

## DCC

Unter `local_lab`: Development Dashboard → Panel **Backend Health / Watchdog** (read-only, Operator-Befehle nur kopieren).
