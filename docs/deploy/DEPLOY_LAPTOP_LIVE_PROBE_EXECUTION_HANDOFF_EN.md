# Deploy Laptop Live Probe Execution Handoff (EN)

Controlled **live probe** (read-only HTTP): plan → execute → result → final gate. No restore, no device write, no systemctl lifecycle changes, no chmod/chown, no delete.

**Input:** `laptop_failure_test_execution_readiness_gate.json`, `live_base_url` (default `http://127.0.0.1:8000`).

**Handoffs:**

| Step | File |
|------|------|
| Plan | `docs/evidence/runtime-results/handoff/laptop_live_probe_plan.json` |
| Execute + result | `docs/evidence/runtime-results/handoff/laptop_live_probe_result.json` |
| Final gate | `docs/evidence/runtime-results/handoff/laptop_live_probe_final_gate.json` |

**API:**  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-plan`  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-execute-readonly` (requires `explicit_execute_live_probe=true`)  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-final-gate`

Codes: `DEPLOY_LAPTOP_LIVE_PROBE_PLAN_*`, `DEPLOY_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_*`, `DEPLOY_LAPTOP_LIVE_PROBE_FINAL_GATE_*`.

If readiness handoff `abnahme_decision` is not `pass`, the plan is at least **review_required** (no artificial OK).
