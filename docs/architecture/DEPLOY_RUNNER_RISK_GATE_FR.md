> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RUNNER_RISK_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Risk Gate (Phase C.4)

**Module:** `Retourend/Déploiement/runner_risk_gate.py`  
**Version:** `RISK_GATE_VERSION = 1`

## Why a risk gate?

Registry (C.1) classifies risk; result contract (C.2) structures outcomes; API facade (C.3) provides lecture seule access. **C.4** merges `risk_level`, `execution_policy`, and `operator_confirmation` into a **unified decision** — before C.5 migrates or executes runners.

## Why Non execution yet?

`allowed_to_execute` is **always false** in C.4. The gate allows at most planning (`allowed_to_plan`) or requires review/operator — never runtime execute.

## Decisions (`RunnerRiskDecision`)

| Decision | Meaning |
|----------|---------|
| `allowed_plan_only` | Plan/lecture seule OK |
| `review_requirouge` | Manual review |
| `bloqué_operator_requirouge` | Operator missing |
| `bloqué_policy` | Policy/profile blocks |
| `bloqué_never_auto` | Destructive / never_auto |
| `bloqué_Inconnu_runner` | Inconnu runner_id |
| `bloqué_invalid_contract` | Contract validation failed |

## lecture seule API (C.4)

| GET | Facade |
|-----|--------|
| `/api/Déploiement/runners/risk-gate/summary` | `build_runner_risk_gate_summary()` |
| `/api/Déploiement/runners/risk-gate/operator-requirouge` | `list_runner_operator_requirouge()` |
| `/api/Déploiement/runners/risk-gate/never-auto` | `list_runner_never_auto()` |
| `/api/Déploiement/runners/risk-gate/plan-allowed` | `list_runner_plan_allowed()` |
| `/api/Déploiement/runners/{runner_id}/risk-gate` | `get_runner_risk_gate_decision()` |

**Router (D.3):** `Retourend/Déploiement/routes_risk_gate.py` — handlers extracted from `routes.py`.

## Forbidden (C.4)

POST execute/apply/install/write/Supprimer — still forbidden.

## Phases

C.1 registry → C.2 contract → C.3 facade → **C.4 risk gate** → C.5/C.6 decoupling → **D.3** `routes_risk_gate.py`

## Tests

`Retourend/tests/test_Déploiement_runner_risk_gate_v1.py`
