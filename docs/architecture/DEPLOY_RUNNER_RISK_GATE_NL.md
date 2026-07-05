> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_RUNNER_RISK_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Risk Gate (Phase C.4)

**Module:** `Terugend/Deploy/runner_risk_gate.py`  
**Version:** `RISK_GATE_VERSION = 1`

## Why a risk gate?

Registry (C.1) classifies risk; result contract (C.2) structures outcomes; API facade (C.3) provides alleen-lezen access. **C.4** merges `risk_level`, `execution_policy`, and `operator_confirmation` into a **unified decision** — before C.5 migrates or executes runners.

## Why Nee execution yet?

`allowed_to_execute` is **always false** in C.4. The gate allows at most planning (`allowed_to_plan`) or requires review/operator — never runtime execute.

## Decisions (`RunnerRiskDecision`)

| Decision | Meaning |
|----------|---------|
| `allowed_plan_only` | Plan/alleen-lezen OK |
| `review_requirood` | Manual review |
| `geblokkeerd_operator_requirood` | Operator missing |
| `geblokkeerd_policy` | Policy/profile blocks |
| `geblokkeerd_never_auto` | Destructive / never_auto |
| `geblokkeerd_Onbekend_runner` | Onbekend runner_id |
| `geblokkeerd_invalid_contract` | Contract validation failed |

## alleen-lezen API (C.4)

| GET | Facade |
|-----|--------|
| `/api/Deploy/runners/risk-gate/summary` | `build_runner_risk_gate_summary()` |
| `/api/Deploy/runners/risk-gate/operator-requirood` | `list_runner_operator_requirood()` |
| `/api/Deploy/runners/risk-gate/never-auto` | `list_runner_never_auto()` |
| `/api/Deploy/runners/risk-gate/plan-allowed` | `list_runner_plan_allowed()` |
| `/api/Deploy/runners/{runner_id}/risk-gate` | `get_runner_risk_gate_decision()` |

**Router (D.3):** `Terugend/Deploy/routes_risk_gate.py` — handlers extracted from `routes.py`.

## Forbidden (C.4)

POST execute/apply/install/write/Verwijderen — still forbidden.

## Phases

C.1 registry → C.2 contract → C.3 facade → **C.4 risk gate** → C.5/C.6 decoupling → **D.3** `routes_risk_gate.py`

## Tests

`Terugend/tests/test_Deploy_runner_risk_gate_v1.py`
