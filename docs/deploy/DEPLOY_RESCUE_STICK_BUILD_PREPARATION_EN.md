# Deploy — Rescue Stick Build Preparation (EN)

Read-only **deploy runners** and API endpoints to prepare the Setuphelfer rescue stick (no ISO build, no USB write).

## Handoff files

| Step | JSON |
|------|------|
| Live OS base decision | `docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json` |
| Component inventory | `docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json` |
| MVP scope gate | `docs/evidence/runtime-results/handoff/rescue_mvp_scope_gate.json` |
| Debian live build plan | `docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json` |
| ISO test matrix | `docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json` |
| Build readiness gate | `docs/evidence/runtime-results/handoff/rescue_build_readiness_gate.json` |

## API (`POST`, prefix `/api/deploy`)

- `/rescue/live-os-base-decision`
- `/rescue/component-inventory`
- `/rescue/mvp-scope-gate`
- `/rescue/debian-live-build-plan`
- `/rescue/iso-test-matrix`
- `/rescue/build-readiness-gate`

Body: `{ "explicit_overwrite": true|false }` — existing handoffs are not overwritten unless `explicit_overwrite` is true.

## Response codes

- `DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_COMPONENT_INVENTORY_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_MVP_SCOPE_GATE_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_ISO_TEST_MATRIX_{OK|REVIEW_REQUIRED|BLOCKED}`
- `DEPLOY_RESCUE_BUILD_READINESS_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`

## Version note

When all gates are **ok/ready**, a manual bump **1.7.x → 1.8.0** is appropriate (new rescue strand, new routes) — **not** auto-applied in this phase.
