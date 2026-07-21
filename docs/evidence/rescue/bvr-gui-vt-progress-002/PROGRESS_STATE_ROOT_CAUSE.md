# Progress State Root Cause

## Why auto-e2e-state stayed at sabrent_waiting

1. Stick mirror of `auto-e2e-state` was not updated on every progress write (only occasional/`mirror_state_to_setup_logs`).
2. `_progress_write` historically always set `status=running` even on shutdown.
3. GUI/TUI preferred orchestration state over `physical-progress`.

## Fix

- Write `canonical-bvr-progress.json` on each progress update and mirror it.
- Project to `physical-progress.json`.
- Finalize with `status=passed|failed` and `terminal=true`.
- Display readers use canonical only; detect drift vs auto-e2e-state.
