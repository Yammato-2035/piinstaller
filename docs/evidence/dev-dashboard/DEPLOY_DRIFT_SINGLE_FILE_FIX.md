# Deploy Drift Single File Fix

- **Generated at:** `2026-05-27`
- **Project version:** `1.7.2`
- **Fix commit:** `2c7e9ee` (`Fix dev dashboard single file deploy drift detection`)
- **Source commit before fix:** `b83c714`
- **Affected file:** `packaging/helpers/setuphelfer-backup-starter.py`

## External runtime gate (before code deploy to `/opt`)

- `./scripts/check-runtime-deploy-gate.sh`: **Exit 14** at analysis time (workspace contained additional uncommitted backend/dashboard changes beyond the packaging helper drift).

## Internal dashboard (before fix, live `/opt` backend)

- `deploy/status.status`: `blocked` or `ready` with `runtime_gate.exit_code` **14** or **20**
- `deploy_drift.status`: **yellow**
- `deploy_drift.files`: included `packaging/helpers/setuphelfer-backup-starter.py` and temporarily `backend/core/dev_dashboard.py` (uncommitted fix in workspace)
- `rescue-iso`: `operator_policy_gate` / preflight blocked due to runtime gate

## SHA256 analysis

| Source | SHA256 |
|--------|--------|
| Workspace worktree | `81ca127229541faf07e2e74d1d8e6d48c94302a053fe85ab1e1d6bfc328165dd` |
| `/opt/setuphelfer` runtime | `a09627d2c672f9330dedaaf609c05573ee4e94dfcdab7bee974abffadac39ca0` |
| `git HEAD` (committed) | `a09627d2c672f9330dedaaf609c05573ee4e94dfcdab7bee974abffadac39ca0` |

## Diff short finding

- Workspace adds uncommitted allowlist entry: `Path("/media/setuphelfer")`
- `/opt` and `git HEAD` agree; runtime is **not** outdated.
- Deploying the dirty workspace file to `/opt` would incorrectly promote a host-only path.

## Root cause

**`workspace_dirty_uncommitted`** with **`dashboard_false_positive`** drift detection (workspace worktree compared directly to `/opt` without checking whether `/opt` already matches `git HEAD`).

Not:

- `runtime_file_outdated` (runtime matches HEAD)
- `deploy_helper_missed_packaging_helper` (file is in deploy manifest)

## Chosen measure

1. **Code fix (minimal):** In `backend/core/dev_dashboard.py`, treat manifest-tracked files as matching when runtime content equals `git HEAD` even if the workspace worktree is dirty (`workspace_dirty_runtime_matches_head`).
2. **Runtime gate alignment:** In `backend/core/dev_dashboard_cockpit.py`, do not fail Phase-0-style runtime gate on yellow `deploy_drift` when `suggested_actions` is only `["none"]`, and allow yellow `consistency` when warnings are only `workspace_dirty` / `workspace_unpushed` while deploy drift is green.
3. **Deploy:** Controlled deploy via `setuphelfer-deploy-helper.service` to publish backend fix to `/opt` (no direct `deploy-to-opt.sh`, no manual `cp`).
4. **Operator hygiene (recommended, not executed by Cursor):** `git restore packaging/helpers/setuphelfer-backup-starter.py` to drop host-only allowlist from the workspace.

## Post-fix verification (workspace code, `/opt` runtime, before deploy)

After `2c7e9ee`, evaluated with `PYTHONPATH=backend` against `/home/volker/piinstaller` and `/opt/setuphelfer`:

| File | `matches` | `reason` |
|------|-----------|----------|
| `packaging/helpers/setuphelfer-backup-starter.py` | **true** | `workspace_dirty_runtime_matches_head` |
| `backend/core/dev_dashboard.py` | **false** | `sha256_mismatch` (fix not yet in `/opt`) |

- `deploy_drift.status` = **yellow** (one actionable backend file pending deploy)
- `deploy_drift.suggested_actions` = `deploy_backend_files`, `restart_backend_manual`
- Unit tests: `test_deploy_drift_green_when_workspace_dirty_but_runtime_matches_head`, `test_runtime_gate_allows_yellow_drift_without_actionable_suggestions`, deploy/regression suites → **OK**

## Deploy step (operator, required for live API)

Cursor could not run `sudo systemctl start setuphelfer-deploy-helper.service` (password required). Operator:

```bash
sudo systemctl start setuphelfer-deploy-helper.service
# then verify:
./scripts/check-runtime-deploy-gate.sh
curl -s http://127.0.0.1:8000/api/dev-dashboard/deploy/status | jq '.runtime_gate.exit_code, .deploy_drift.status'
curl -s http://127.0.0.1:8000/api/dev-dashboard/rescue-iso/status | jq '.status, .usb_write.allowed'
```

## Post-deploy expectation

- `deploy_drift.status` = **green** (packaging helper stays green; `dev_dashboard.py` + cockpit synced)
- `runtime_gate.exit_code` = **0**
- `rescue-iso` no longer blocked solely because of packaging-helper deploy drift
- `usb_write.allowed` remains **false**

## Live API snapshot (before deploy to `/opt`, commit `2c7e9ee` only on GitHub)

- `GET /api/dev-dashboard/deploy/status`: `runtime_gate.exit_code` = **14**, `deploy_drift.status` = **yellow**
- `GET /api/dev-dashboard/rescue-iso/status`: `status` = **red**, `usb_write.allowed` = **false**

## Runtime-Abnahme (nach `setuphelfer-deploy-helper.service`, Operator 2026-05-27)

| Check | Ergebnis |
|-------|----------|
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** — OK (Version, Pfad, deploy_drift/Manifest) |
| `deploy/status` → `runtime_gate.exit_code` | **0** |
| `deploy/status` → `deploy_drift.status` | **green** |
| `deploy/status` → `status` | **success** |
| `rescue-iso/status` → `status` | **yellow** (nicht mehr rot wegen Deploy-Drift) |
| `rescue-iso/status` → `operator_policy_gate` | **review_required**, `blocked_reasons` = `[]` |
| `rescue-iso/status` → `usb_write.allowed` | **false** |

**Fazit:** Deploy-Drift-Auftrag **abgenommen**. Rescue bleibt gelb aus Build-/Policy-Gründen (`next_operator_action`: `operator_policy_required`), nicht wegen des Packaging-Helper-False-Positives.

**Nächster Prompt:** `RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD`
