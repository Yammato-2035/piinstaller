# Next Prompt Selection (Latest)

**Selected:** `RUNTIME_DEPLOY_DRIFT_CLEANUP_AND_COCKPIT_LIVE_SYNC`  
**At:** 2026-05-27T23:45:00Z · **HEAD:** `84eb309`

## Reason

- `./scripts/check-runtime-deploy-gate.sh` → **Exit 14** (`deploy_drift_backend_files`)
- `safe_test_mode` = **LOCKED**
- Workspace `backend/app.py` / `dev_dashboard_manual_command_runs.py` not synced to `/opt`
- Cockpit dev URL: use Vite terminal port (e.g. **3002**), not fixed **5173**

## Deferred

`RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` — blocked by `deploy_drift_backend_files` and `runtime_phase0_gate` until gate **Exit 0**.

## After operator deploy-helper sync

Recommended next: `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`

JSON: `NEXT_PROMPT_SELECTION_LATEST.json`
