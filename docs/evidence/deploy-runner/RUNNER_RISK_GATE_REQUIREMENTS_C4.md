# Runner Risk Gate Requirements (Phase C.4)

**HEAD-Basis:** `ef20b6a` | **Runner:** 115

## risk_level (Registry)

`read_only`, `template_write`, `evidence_write`, `local_runtime_change`, `system_change`, `device_write`, `destructive`

## execution_policy (Registry)

`never_auto`, `manual_only`, `operator_confirmed`, `lab_only`, `disabled`

## Entscheidungsmatrix (C.4)

| risk_level | execution_policy | operator_confirmed | Entscheidung |
|------------|------------------|--------------------|--------------|
| read_only | manual_only / lab_only | false | `allowed_plan_only` |
| evidence_write | lab_only | false | `allowed_plan_only` |
| template_write | manual_only / lab_only | false | `review_required` |
| local_runtime_change | operator_confirmed | false | `blocked_operator_required` |
| system_change | operator_confirmed | false | `blocked_operator_required` |
| device_write / destructive (uses_device_write) | operator_confirmed | false | `blocked_operator_required` |
| destructive | never_auto | false / true | `blocked_never_auto` |
| unknown runner_id | — | — | `blocked_unknown_runner` |
| invalid contract | — | — | `blocked_invalid_contract` |
| disabled policy | disabled | — | `blocked_policy` |

**C.4:** `allowed_to_execute` ist **immer false** — auch bei Operator-Bestätigung.

## Betroffene Runner (Ist, Registry)

| Gruppe | Anzahl |
|--------|--------|
| Gesamt | 115 |
| destructive (`blocked_never_auto`) | 8 |
| uses_device_write (heuristisch) | 8 |
| sudo | 23 |
| system_change | 5 |
| unknown category | 19 |

**Gate-Summary (Default-Kontext):** `allowed_plan_only` 62, `review_required` 12, `blocked_operator_required` 33, `blocked_never_auto` 8

## Warum C.4 noch keine Ausführung erlaubt

Risk Gate liefert nur **Entscheidungen** für Planung und spätere C.5-Migration. Kein Execute-Pfad, keine POST-Routen, keine Runner-Imports. Runtime-Freigabe kommt erst nach C.5 + explizitem Risk-Gate-Upgrade.

## Destructive Runner (never_auto)

- `runner_rescue_build_readiness_gate`
- `runner_rescue_debian_live_build_inputs`
- `runner_rescue_dry_build_orchestration`
- `runner_rescue_iso_build_execution_plan`
- `runner_rescue_iso_readiness_pipeline`
- `runner_rescue_pseudo_boot_integration`
- `runner_rescue_runtime_assembly_pipeline`
- `runner_rescue_storage_discovery`
