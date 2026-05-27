# Roadmap Runtime-Drift Delta

**Datum:** 2026-05-27 · **HEAD:** `84eb309`

## Geändert (ehrlich)

| Bereich | Vorher (implizit) | Nachher |
|---------|-------------------|---------|
| Runtime-Governance / Phase-0 | teils als „grün genug“ lesbar | **gelb/blockiert** — Gate Exit **14** |
| `safe_test_mode` | — | **LOCKED** bis Gate Exit 0 |
| Dev-Cockpit live unter `/opt` | Hinweis „vor Rescue prüfen“ | **gelb/offen** — API-Modul fehlt in `/opt` |
| Command Logging (Evidence) | **grün/completed** | unverändert grün |
| TERMINAL_A_READONLY | completed | unverändert |
| API-Tests venv | grün | unverändert |
| API-Tests System-Python | gelb (11 skipped) | unverändert |
| Nächster Prompt | `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` | **`RUNTIME_DEPLOY_DRIFT_CLEANUP_AND_COCKPIT_LIVE_SYNC`** bis Gate 0 |
| Rescue ISO Manual Build | empfohlen | **blockiert** durch Runtime-Gate |

## Bleibt blockiert

- `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` bis `./scripts/check-runtime-deploy-gate.sh` Exit **0**
- Runtime-Tests gegen Port **8000** (Funktionsabnahme) während Gate rot
- Backup / Restore / Verify Deep / ISO-Build (wie im Auftrag ausgeschlossen)

## Nach erfolgreichem Deploy-Helper (Operator)

- `runtime_gate` → grün
- `deploy_drift` → grün
- `safe_test_mode` → UNLOCKED (read-only Governance)
- Nächster Prompt → `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`

JSON: `roadmap_runtime_drift_delta_latest.json`
