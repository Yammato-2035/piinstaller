# Deploy-Helper-Sync — Ergebnis

**Datum:** 2026-05-27 · **HEAD:** `21af233` · **Operator-Freigabe:** `DEPLOY_HELPER_SYNC_FREIGEGEBEN`

## Kurzfassung

| Prüfung | Ergebnis |
|---------|----------|
| Gate **vor** Agent-Deploy-Versuch | Exit **0** (bereits grün — `/opt` bereits synchron) |
| `sudo systemctl start setuphelfer-deploy-helper.service` | **Nicht ausgeführt** (sudo: Passwort erforderlich in Agent-Shell) |
| Gate **nach** Prüfung | Exit **0** |
| `deploy_drift` | **green** |
| `safe_test_mode` | **UNLOCKED** |
| `manual-command-runs` API | HTTP **200** |
| `/opt` Bundle | `index-CtMitZ58.js` (2026-05-27 22:41), enthält `manualCommandRuns`, `readyTitle` |

## Drift-Nachweis (vor/nach)

| Datei | Workspace SHA | `/opt` SHA |
|-------|---------------|------------|
| `backend/app.py` | `171d4037…` | `171d4037…` (identisch) |
| `backend/core/dev_dashboard_manual_command_runs.py` | vorhanden | vorhanden |

`_compute_deploy_drift` → `status=green`, `suggested_actions=['none']`.

## Deploy-Helper (systemd)

```text
sudo systemctl start setuphelfer-deploy-helper.service
→ sudo: Passwort erforderlich (kein TTY)
Service-Status: inactive (dead)
journalctl: keine Einträge sichtbar (Agent ohne system-journal-Rechte)
```

**Interpretation:** Der dokumentierte Drift war zum Laufzeitpunkt bereits behoben (vermutlich früherer Operator-Deploy, Bundle-Zeitstempel 22:41). Ein erneuter Helper-Lauf durch den Agenten scheiterte nur an sudo — kein manueller `/opt`-Kopier-Workaround.

Falls ein frischer Deploy-Log gewünscht ist, Operator lokal:

```bash
sudo systemctl start setuphelfer-deploy-helper.service
journalctl -u setuphelfer-deploy-helper.service -n 80 --no-pager
./scripts/check-runtime-deploy-gate.sh
```

## Live-API (Gate 0)

- `project_version`: **1.7.2**
- `backend_runtime_path`: `/opt/setuphelfer/backend`
- `runtime_gate.passed`: **true**
- `deploy_drift.status`: **green**
- `safe_test_mode.mode`: **UNLOCKED**

JSON: `deploy_helper_sync_result_latest.json`
