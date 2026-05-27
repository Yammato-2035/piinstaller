# Runtime / Deploy-Drift Cleanup — Audit

**Stand:** 2026-05-27  
**Branch:** `main`  
**HEAD:** `84eb309` (letzter gepushter Commit)  
**Phase-0-Gate:** Exit **14** (`deploy_drift_backend_files`)  
**Modus:** Nur statische Analyse — `runtime_gate_blocked_static_analysis_only=true`

## Gate

```text
./scripts/check-runtime-deploy-gate.sh → Exit 14
Evaluator: deploy_drift.status=yellow, suggested_actions=[deploy_backend_files, restart_backend_manual]
```

## Drift-Ursache

| Datei (Manifest) | Workspace | `/opt/setuphelfer` | Vergleich |
|------------------|-----------|-------------------|-----------|
| `backend/app.py` | SHA `171d4037…`, ~770 259 B, 2026-05-27 22:18 | SHA `5ceb1a05…`, ~769 922 B, 2026-05-26 22:51 | **Abweichung** (`compared_by_size_mtime` — Datei > Hash-Limit) |

**Interpretation:** Der Workspace (Commits `5786eb3` u. a. `GET /api/dev-dashboard/manual-command-runs`, `84eb309` Roadmap/Cockpit-UI) liegt **vor** der produktiven Runtime unter `/opt`. Kein False-Positive am Packaging-Helper (`setuphelfer-backup-starter.py` war früher separat behoben).

Zusätzlich (nicht einzeln im Drift-Manifest, aber relevant für Live-Cockpit):

- `/opt/setuphelfer/backend/core/dev_dashboard_manual_command_runs.py` — **fehlt**
- Workspace enthält Modul + Route in `app.py`
- Frontend unter `/opt` kann teilweise aktueller sein; Backend-API für Command Runs ist ohne Deploy **nicht** live.

## Empfohlene Behebung (Operator)

1. Explizit freigeben: `DEPLOY_HELPER_SYNC_FREIGEGEBEN`
2. `sudo systemctl start setuphelfer-deploy-helper.service`
3. `./scripts/check-runtime-deploy-gate.sh` → erwartet Exit **0**
4. Optional manueller Backend-Restart nur wenn Gate Exit **15** meldet (hier: **14** → primär Datei-Deploy)

**Nicht** in diesem Lauf: automatischer Deploy, `sudo` ohne Freigabe, Gate-Logik abschwächen.

## `may_deploy_helper_fix`

**true** — erwarteter Sync von `backend/app.py`, `backend/core/dev_dashboard_manual_command_runs.py` und zugehörigem Frontend-Bundle.

## `must_not_touch`

- Unrelated dirty: `ckb-next`, `VERSION`, Rescue-/Lab-Evidence ohne Auftrag
- `packaging/helpers/setuphelfer-backup-starter.py` (Host-Pfad-Drift `/media/setuphelfer` — separater Operator-Entscheid)
- Safety-Gates / Evaluator-Exit-Codes

## Cockpit-Ports (lokal)

| Port | Status |
|------|--------|
| 8000 | listening (Backend) |
| 5173 | **not listening** (nur `dev:tauri` / strict Tauri) |
| 3001 | listening (anderer Prozess) |
| 3002 | listening (Vite `dev:cockpit`, Fallback) |

**Korrekte Dev-Cockpit-URL (aktuell):** `http://127.0.0.1:3002/?window=cockpit`

Machine-readable: `runtime_deploy_drift_cleanup_audit_latest.json`
