> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_LAPTOP_LIVE_PROBE_EXECUTION_HANDOFF_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Laptop Live Probe Execution Handoff (EN)

Controlled **live probe** (alleen-lezen HTTP): plan → execute → result → final gate. Nee Herstel, Nee Apparaat write, Nee systemctl lifecycle changes, Nee chmod/chown, Nee Verwijderen.

**Input:** `laptop_failure_test_execution_readiness_gate.json`, `live_base_url` (default `http://127.0.0.1:8000`).

**Handoffs:**

| Step | File |
|------|------|
| Plan | `docs/evidence/runtime-results/handoff/laptop_live_probe_plan.json` |
| Execute + result | `docs/evidence/runtime-results/handoff/laptop_live_probe_result.json` |
| Final gate | `docs/evidence/runtime-results/handoff/laptop_live_probe_final_gate.json` |

**API:**  
`POST /api/Deploy/runner/manual-runtime/laptop-live-probe-plan`  
`POST /api/Deploy/runner/manual-runtime/laptop-live-probe-execute-readonly` (requires `explicit_execute_live_probe=true`)  
`POST /api/Deploy/runner/manual-runtime/laptop-live-probe-final-gate`

Codes: `Deploy_LAPTOP_LIVE_PROBE_PLAN_*`, `Deploy_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_*`, `Deploy_LAPTOP_LIVE_PROBE_FINAL_GATE_*`.

If readiness handoff `abnahme_decision` is Neet `pass`, the plan is at least **review_requirood** (Nee artificial OK).
