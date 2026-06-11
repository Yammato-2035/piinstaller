# Deploy Runner Risk Gate (Phase C.4)

**Modul:** `backend/deploy/runner_risk_gate.py`  
**Version:** `RISK_GATE_VERSION = 1`

## Warum Risk Gate?

Registry (C.1) klassifiziert Risiko; Result Contract (C.2) strukturiert Ergebnisse; API Facade (C.3) liefert read-only Zugriff. **C.4** führt `risk_level`, `execution_policy` und `operator_confirmation` zu einer **einheitlichen Entscheidung** zusammen — bevor in C.5 Runner migriert oder ausgeführt werden.

## Warum noch keine Ausführung?

`allowed_to_execute` ist in C.4 **immer false**. Das Gate erlaubt höchstens Planung (`allowed_to_plan`) oder verlangt Review/Operator — nie Runtime-Execute.

## Entscheidungen (`RunnerRiskDecision`)

| Decision | Bedeutung |
|----------|-----------|
| `allowed_plan_only` | Plan/Read-only OK |
| `review_required` | Manuelle Prüfung |
| `blocked_operator_required` | Operator fehlt |
| `blocked_policy` | Policy/Profil blockiert |
| `blocked_never_auto` | Destructive / never_auto |
| `blocked_unknown_runner` | Unbekannte runner_id |
| `blocked_invalid_contract` | Contract-Validierung fehlgeschlagen |

## Read-only API (C.4)

| GET | Facade |
|-----|--------|
| `/api/deploy/runners/risk-gate/summary` | `build_runner_risk_gate_summary()` |
| `/api/deploy/runners/risk-gate/operator-required` | `list_runner_operator_required()` |
| `/api/deploy/runners/risk-gate/never-auto` | `list_runner_never_auto()` |
| `/api/deploy/runners/risk-gate/plan-allowed` | `list_runner_plan_allowed()` |
| `/api/deploy/runners/{runner_id}/risk-gate` | `get_runner_risk_gate_decision()` |

**Router (D.3):** `backend/deploy/routes_risk_gate.py` — Handler aus `routes.py` ausgelagert.

## Verboten (C.4)

POST execute/apply/install/write/delete — unverändert verboten.

## Phasen

C.1 Registry → C.2 Contract → C.3 Facade → **C.4 Risk Gate** → C.5/C.6 Decoupling → **D.3** `routes_risk_gate.py`

## Tests

`backend/tests/test_deploy_runner_risk_gate_v1.py`
