# Development Control Cockpit — Live-Runtime-Validierung

**Stand:** 2026-05-15  
**Workspace-Commit:** `242eb42` (+ lokale Fixes Deploy-Validierung)

## Ergebnis (echte Runtime unter `/opt/setuphelfer`)

| Prüfung | Ergebnis |
|---------|----------|
| `GET /api/version` | HTTP 200, `project_version` **1.7.1** |
| `GET /api/dev-dashboard/status` | HTTP 200, Cockpit-Felder vorhanden |
| `deploy_drift` | **green** (Workspace `/home/volker/piinstaller` vs. Runtime `/opt/setuphelfer`, Manifest-Match) |
| `runtime_gate` (Cockpit) | **yellow** — `setuphelfer-backend.service` inactive bei manuellem Start; `consistency` yellow (`workspace_dirty`, `workspace_unpushed`) |
| `safe_test_mode` | **LOCKED** (korrekt bei nicht bestandenem Runtime-Gate) |
| `GET /api/dev-dashboard/cursor-meta-prompt` | HTTP 200, echter Prompt (~1 KB), Findings/Risiken/Verbote enthalten |
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 10**, wenn Dienst nicht als `active` gemeldet wird; **Exit 0** bei laufender API + grünem Deploy-Drift (Evaluator) |

## Deploy (diese Session)

- Backend: `rsync`/`install` nach `/opt/setuphelfer/backend` (inkl. `dev_dashboard_cockpit.py`)
- Docs/Evidence: `docs/evidence`, `docs/roadmap`, `docs/dev-dashboard` nach `/opt` synchronisiert
- Manifest: `build/deploy/setuphelfer-deploy-manifest.json` (Workspace + Runtime)
- Workspace-Root für Drift: `/opt/setuphelfer/.env` mit `SETUPHELFER_DEV_WORKSPACE_ROOT=/home/volker/piinstaller` und Leselogik in `dev_dashboard.py`
- Frontend-`dist/`: teilweise blockiert (Dateien nur `setuphelfer`-Owner, nicht gruppenbeschreibbar); Drift für Whitelist-Quellen dennoch **green**

## Bekannte Blocker

1. **Vollständiger Deploy:** `sudo ./scripts/deploy-to-opt.sh` empfohlen (benötigt sudo-Passwort); ohne sudo nur Teilsync.
2. **systemd:** `setuphelfer-backend.service` nach Teilsync/Port-Konflikten ggf. `activating` — manuell prüfen: `sudo systemctl restart setuphelfer-backend.service`.
3. **Gate-Skript:** Bei `if python3 …; then` setzt Bash `$?` nach fehlgeschlagenem `if`-Test auf 0 — Evaluator-Exit manuell mit `runtime_deploy_gate_eval.py` prüfen.
4. **Safe Test Mode:** Bleibt LOCKED bei git-dirty Workspace (echte Daten, kein Fake-Grün).

## Keine Aktionen in dieser Validierung

Kein Backup, Restore, Hardwaretest, `apt upgrade`, automatisches Paketupdate.
