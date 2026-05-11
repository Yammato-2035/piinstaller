# Deploy Laptop Live Probe Execution Handoff (DE)

Kontrollierte **Live-Probe** (HTTP read-only) mit Plan → Ausführung → Ergebnis → Final-Gate. Kein Restore, kein Device-Write, keine systemctl-Lifecycle-Aenderungen, kein chmod/chown, kein Delete.

**Input:** `laptop_failure_test_execution_readiness_gate.json`, `live_base_url` (Default `http://127.0.0.1:8000`).

**Handoffs:**

| Schritt | Datei |
|--------|--------|
| Plan | `docs/evidence/runtime-results/handoff/laptop_live_probe_plan.json` |
| Execute + Result | `docs/evidence/runtime-results/handoff/laptop_live_probe_result.json` |
| Final Gate | `docs/evidence/runtime-results/handoff/laptop_live_probe_final_gate.json` |

**API:**  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-plan`  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-execute-readonly` (nur mit `explicit_execute_live_probe=true`)  
`POST /api/deploy/runner/manual-runtime/laptop-live-probe-final-gate`

Codes: `DEPLOY_LAPTOP_LIVE_PROBE_PLAN_*`, `DEPLOY_LAPTOP_LIVE_PROBE_EXECUTE_READONLY_*`, `DEPLOY_LAPTOP_LIVE_PROBE_FINAL_GATE_*`.

`abnahme_decision != pass` im Readiness-Handoff erzwingt mindestens **review_required** im Plan (kein kuenstliches OK).
