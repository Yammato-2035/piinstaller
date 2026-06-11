# Deploy Runner Risk Gate Contract (Phase C.4)

## Statische Prüfung

- Neue Routen: **GET only**, Pfade ohne execute/apply/install/write/delete
- Responses enthalten `RunnerRiskGateDecision` + `allowed_to_execute: false`
- Facade importiert nur `runner_registry`, `runner_result_contract`, `runner_risk_gate`
- Keine Runtime-Smokes bei Gate Exit 20

## Decision-Pflichtfelder

`runner_id`, `decision`, `allowed_to_execute`, `allowed_to_plan`, `requires_operator`, `requires_runtime_gate`, `requires_lab_profile`, `requires_hardware_presence`, `risk_level`, `execution_policy`, `reasons`, `warnings`, `errors`, `next_required_actions`
