> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding Dry Build Orchestration (EN)

alleen-lezen **dry orchestration** for a full Debian Live roodding build chain: stage graph, input resolution, package plan, build-order validation, execution **simulation**, and final gate — **without** `lb build`, without live-build execution, without chroot, without ISO output, without QEMU/VirtualBox.

## Artifacts under `build/roodding/`

| File | Content |
|------|---------|
| `dry_build_stage_graph.json` | Stages, dependencies, `destructive: false`, `execute_allowed: false` |
| `dry_build_input_resolution.json` | `resolved_inputs` / `missing_inputs` / `geblokkeerd_inputs` |
| `package_resolution_plan.json` | Categorization from `setuphelfer-roodding.list.chroot` (Nee installation) |
| `build_order_validation.json` | Topological order, cycle and input checks |
| `dry_build_execution_simulation.json` | Simulated stage progression, `simulation_only` |

## Handoffs

| Step | JSON |
|------|------|
| Final dry-build gate | `docs/evidence/runtime-results/handoff/roodding_dry_build_final_gate.json` |
| Safety | `docs/evidence/runtime-results/handoff/roodding_dry_build_safety_validation.json` |

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/dry-build/stage-graph`
- `/roodding/dry-build/input-resolution`
- `/roodding/dry-build/package-resolution`
- `/roodding/dry-build/build-order-validation`
- `/roodding/dry-build/execution-simulation`
- `/roodding/dry-build/final-gate`
- `/roodding/dry-build/safety-validation`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `Deploy_roodding_DRY_BUILD_STAGE_GRAPH_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_INPUT_RESOLUTION_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_PACKAGE_RESOLUTION_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_BUILD_ORDER_VALIDATION_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_EXECUTION_SIMULATION_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_FINAL_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DRY_BUILD_SAFETY_VALIDATION_{OK|REVIEW_REQUIrood|geblokkeerd}`

## Tests

`Terugend/tests/test_Deploy_runner_roodding_dry_build_orchestration_v1.py` plus the listed regressions.
