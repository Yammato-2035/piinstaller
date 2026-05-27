# Dev Dashboard Read-only Command Logging — Summary

**Datum:** 2026-05-27  
**HEAD (Basis):** `40cde4e` → Commit folgt

## Gate

`./scripts/check-runtime-deploy-gate.sh` → **Exit 0**

## API-Test-Skip-Ursache

System-`/usr/bin/python3` ohne `fastapi` → **11 skipped**.  
`backend/venv/bin/python3` → **34 passed, 0 skipped**.

## Tests (dieser Lauf)

| Suite | Ergebnis |
|-------|----------|
| `backend/venv/bin/python3 -m unittest backend.tests.test_dev_dashboard_v1` | 34 ok, 0 skipped |
| `backend/venv/bin/python3 -m unittest backend.tests.test_dev_dashboard_manual_command_runs_v1` | ok |
| `npm --prefix frontend run build` | ok |
| `npm --prefix frontend run test -- --run` | 44 passed |

## Neue Struktur

- `docs/evidence/dev-dashboard/manual_command_runs/` + Schema + Beispiel + Triage-Run JSON
- `backend/core/dev_dashboard_manual_command_runs.py`
- `GET /api/dev-dashboard/manual-command-runs`
- `ManualCommandRunsPanel.tsx` (read-only)

## Keine Execute-Funktionen

Kein POST auf manual-command-runs, kein Shell aus dem Dashboard.

## Ampel nach Feature

| Bereich | Status |
|---------|--------|
| Command-Run-Logging (Struktur + API + UI Code) | **grün** (nach Deploy: live unter /opt) |
| API-Tests mit venv | **grün** |
| API-Tests mit System-python3 only | **gelb** (11 skipped) |
| Vite :5173 Cockpit | **nur wenn Dev-Server läuft** |
| backup/restore/rescue | **rot/gelb** unverändert |

## Nächster Prompt

`RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`
