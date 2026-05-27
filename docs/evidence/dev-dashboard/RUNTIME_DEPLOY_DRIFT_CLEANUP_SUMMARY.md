# Runtime Deploy Drift Cleanup — Summary

**Datum:** 2026-05-27 · **Modus:** Dokumentation + statische Analyse (kein Deploy, kein sudo)

## Ergebnis

| Prüfung | Vorher | Nachher (dieser Lauf) |
|---------|--------|------------------------|
| Phase-0-Gate | Exit **14** | Exit **14** (unverändert — erwartet) |
| `safe_test_mode` | LOCKED | LOCKED |
| Deploy-Helper-Sync | — | **nicht ausgeführt** (kein `DEPLOY_HELPER_SYNC_FREIGEGEBEN`) |

## Ursache

Workspace `84eb309` enthält Backend-Änderungen (`backend/app.py`, `dev_dashboard_manual_command_runs.py`), die unter `/opt/setuphelfer` fehlen bzw. veraltet sind → `deploy_drift_backend_files`.

## Cockpit-Ports

- **5173:** nicht listening
- **3001:** listening (anderer Prozess)
- **3002:** Vite `dev:cockpit`
- **8000:** Backend API

**Cockpit-URL:** `http://127.0.0.1:3002/?window=cockpit`

## Tests (ohne Runtime-Funktionstests gegen 8000)

| Suite | Ergebnis |
|-------|----------|
| `npm run build` | OK |
| Vitest `--run` | **44** passed, **10** files |
| `unittest` (venv) | **40** OK |
| Roadmap JSON | valid |

## Nächster Schritt (Operator)

1. `DEPLOY_HELPER_SYNC_FREIGEGEBEN` schreiben
2. `sudo systemctl start setuphelfer-deploy-helper.service`
3. `./scripts/check-runtime-deploy-gate.sh` → Ziel Exit **0**
4. Dann Prompt: `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`

JSON: `runtime_deploy_drift_cleanup_summary_latest.json`
