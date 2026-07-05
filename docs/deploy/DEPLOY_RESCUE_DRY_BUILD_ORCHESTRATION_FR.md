> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours Dry Build Orchestration (EN)

lecture seule **dry orchestration** for a full Debian Live Secours build chain: stage graph, input resolution, package plan, build-order validation, execution **simulation**, and final gate — **without** `lb build`, without live-build execution, without chroot, without ISO output, without QEMU/VirtualBox.

## Artifacts under `build/Secours/`

| File | Content |
|------|---------|
| `dry_build_stage_graph.json` | Stages, dependencies, `destructive: false`, `execute_allowed: false` |
| `dry_build_input_resolution.json` | `resolved_inputs` / `missing_inputs` / `bloqué_inputs` |
| `package_resolution_plan.json` | Categorization from `setuphelfer-Secours.list.chroot` (Non installation) |
| `build_order_validation.json` | Topological order, cycle and input checks |
| `dry_build_execution_simulation.json` | Simulated stage progression, `simulation_only` |

## Handoffs

| Step | JSON |
|------|------|
| Final dry-build gate | `docs/evidence/runtime-results/handoff/Secours_dry_build_final_gate.json` |
| Safety | `docs/evidence/runtime-results/handoff/Secours_dry_build_safety_validation.json` |

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/dry-build/stage-graph`
- `/Secours/dry-build/input-resolution`
- `/Secours/dry-build/package-resolution`
- `/Secours/dry-build/build-order-validation`
- `/Secours/dry-build/execution-simulation`
- `/Secours/dry-build/final-gate`
- `/Secours/dry-build/safety-validation`

Body: `{ "explicit_overwrite": true|false }`.

## Response codes

- `Déploiement_Secours_DRY_BUILD_STAGE_GRAPH_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_INPUT_RESOLUTION_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_PACKAGE_RESOLUTION_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_BUILD_ORDER_VALIDATION_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_EXECUTION_SIMULATION_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_FINAL_GATE_{READY|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DRY_BUILD_SAFETY_VALIDATION_{OK|REVIEW_REQUIrouge|bloqué}`

## Tests

`Retourend/tests/test_Déploiement_runner_Secours_dry_build_orchestration_v1.py` plus the listed regressions.
