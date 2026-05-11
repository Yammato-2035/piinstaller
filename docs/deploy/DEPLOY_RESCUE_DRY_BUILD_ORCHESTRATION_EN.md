# Deploy — Rescue Dry Build Orchestration (EN)

Read-only **dry orchestration** for a full Debian Live rescue build chain: stage graph, input resolution, package plan, build-order validation, execution **simulation**, and final gate — **without** `lb build`, without live-build execution, without chroot, without ISO output, without QEMU/VirtualBox.

## Artifacts under `build/rescue/`

| File | Content |
|------|---------|
| `dry_build_stage_graph.json` | Stages, dependencies, `destructive: false`, `execute_allowed: false` |
| `dry_build_input_resolution.json` | `resolved_inputs` / `missing_inputs` / `blocked_inputs` |
| `package_resolution_plan.json` | Categorization from `setuphelfer-rescue.list.chroot` (no installation) |
| `build_order_validation.json` | Topological order, cycle and input checks |
| `dry_build_execution_simulation.json` | Simulated stage progression, `simulation_only` |

## Handoffs

| Step | JSON |
|------|------|
| Final dry-build gate | `docs/evidence/runtime-results/handoff/rescue_dry_build_final_gate.json` |
| Safety | `docs/evidence/runtime-results/handoff/rescue_dry_build_safety_validation.json` |

## API (`POST`, prefix `/api/deploy`)

- `/rescue/dry-build/stage-graph`
- `/rescue/dry-build/input-resolution`
- `/rescue/dry-build/package-resolution`
- `/rescue/dry-build/build-order-validation`
- `/rescue/dry-build/execution-simulation`
- `/rescue/dry-build/final-gate`
- `/rescue/dry-build/safety-validation`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_{OK|REVIEW_REQUIRED|BLOCKED}`

## Tests

`backend/tests/test_deploy_runner_rescue_dry_build_orchestration_v1.py` plus the listed regressions.
