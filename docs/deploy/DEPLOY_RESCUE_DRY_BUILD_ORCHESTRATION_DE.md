# Deploy — Rescue Dry Build Orchestration (DE)

Read-only **Dry-Orchestrierung** fuer eine vollstaendige Debian-Live-Rescue-Build-Kette: Stage-Graph, Input-Aufloesung, Paketplan, Build-Reihenfolge-Check, Ausfuehrungs-**Simulation** und Final-Gate — **ohne** `lb build`, ohne `live-build`-Execute, ohne Chroot, ohne ISO-Ausgabe, ohne QEMU/VirtualBox.

## Artefakte unter `build/rescue/`

| Datei | Inhalt |
|-------|--------|
| `dry_build_stage_graph.json` | Stages, Abhaengigkeiten, `destructive: false`, `execute_allowed: false` |
| `dry_build_input_resolution.json` | `resolved_inputs` / `missing_inputs` / `blocked_inputs` |
| `package_resolution_plan.json` | Kategorisierung aus `setuphelfer-rescue.list.chroot` (keine Installation) |
| `build_order_validation.json` | Topologische Ordnung, Zyklus- und Input-Checks |
| `dry_build_execution_simulation.json` | Simulierte Stage-Progression, `simulation_only` |

## Handoffs

| Schritt | JSON |
|--------|------|
| Final Dry-Build-Gate | `docs/evidence/runtime-results/handoff/rescue_dry_build_final_gate.json` |
| Safety | `docs/evidence/runtime-results/handoff/rescue_dry_build_safety_validation.json` |

## API (`POST`, Prefix `/api/deploy`)

- `/rescue/dry-build/stage-graph`
- `/rescue/dry-build/input-resolution`
- `/rescue/dry-build/package-resolution`
- `/rescue/dry-build/build-order-validation`
- `/rescue/dry-build/execution-simulation`
- `/rescue/dry-build/final-gate`
- `/rescue/dry-build/safety-validation`

Body: `{ "explicit_overwrite": true|false }`.

## Response-Codes

- `DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`

## Tests

`backend/tests/test_deploy_runner_rescue_dry_build_orchestration_v1.py` und die genannten Regressionen.
