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

Nach local_lab-Smoke **release wiederherstellen** vor QEMU/Produktionspfaden. Unter release muss `GET /api/dev-dashboard/backend-health` → **404 PROFILE_ROUTE_BLOCKED** (nicht HTTP 200).

**Ports:** API `:8000`, UI/DCC `:3001`, nginx `:8080` (nicht DCC), QEMU-Proxy `:8001`, Gast `http://10.0.2.2:8001`. Registry: `config/runtime_ports.json`; Healthcheck setzt `runtime_ports_source` aus `/opt`. `curl: (7) on :8000` = Backend down, nicht Profilblock. Siehe `docs/dev-dashboard/PORTS_AND_PROFILES.md`, Live-Ingest `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md`.

## Einmaliger Healthcheck (ohne sudo)

```bash
cd /home/volker/piinstaller
./scripts/dev-dashboard/check-backend-health.sh
cat docs/evidence/dev-dashboard/backend_health_latest.json | python3 -m json.tool
```

Exit-Codes: `0` ok, `1` warning, `2` blocked.

### Evidence-Pfade

- Standard: `$REPO_ROOT/docs/evidence/dev-dashboard/` (Repo-Root aus Skriptpfad oder `SETUPHELFER_REPO_ROOT`).
- Override: `SETUPHELFER_HEALTH_EVIDENCE_DIR=/pfad/zum/verzeichnis`.
- Dateien werden mit **`chmod 664`** geschrieben (Backend-User `setuphelfer` muss lesen können).

Wenn die API `permission denied` meldet: Healthcheck erneut ausführen oder `chmod 664` auf `backend_health_latest.json` unter `/opt/setuphelfer/docs/evidence/dev-dashboard/`.

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
