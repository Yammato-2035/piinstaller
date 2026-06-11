# Deploy Runner Risk Gate (Phase C.4)

**Module:** `backend/deploy/runner_risk_gate.py`  
**Version:** `RISK_GATE_VERSION = 1`

## Why a risk gate?

Registry (C.1) classifies risk; result contract (C.2) structures outcomes; API facade (C.3) provides read-only access. **C.4** merges `risk_level`, `execution_policy`, and `operator_confirmation` into a **unified decision** — before C.5 migrates or executes runners.

## Why no execution yet?

`allowed_to_execute` is **always false** in C.4. The gate allows at most planning (`allowed_to_plan`) or requires review/operator — never runtime execute.

## Decisions (`RunnerRiskDecision`)

| Decision | Meaning |
|----------|---------|
| `allowed_plan_only` | Plan/read-only OK |
| `review_required` | Manual review |
| `blocked_operator_required` | Operator missing |
| `blocked_policy` | Policy/profile blocks |
| `blocked_never_auto` | Destructive / never_auto |
| `blocked_unknown_runner` | Unknown runner_id |
| `blocked_invalid_contract` | Contract validation failed |

## Read-only API (C.4)

| GET | Facade |
|-----|--------|
| `/api/deploy/runners/risk-gate/summary` | `build_runner_risk_gate_summary()` |
| `/api/deploy/runners/risk-gate/operator-required` | `list_runner_operator_required()` |
| `/api/deploy/runners/risk-gate/never-auto` | `list_runner_never_auto()` |
| `/api/deploy/runners/risk-gate/plan-allowed` | `list_runner_plan_allowed()` |
| `/api/deploy/runners/{runner_id}/risk-gate` | `get_runner_risk_gate_decision()` |

**Router (D.3):** `backend/deploy/routes_risk_gate.py` — handlers extracted from `routes.py`.

## Forbidden (C.4)

POST execute/apply/install/write/delete — still forbidden.

## Phases

C.1 registry → C.2 contract → C.3 facade → **C.4 risk gate** → C.5/C.6 decoupling → **D.3** `routes_risk_gate.py`

## Tests

`backend/tests/test_deploy_runner_risk_gate_v1.py`
