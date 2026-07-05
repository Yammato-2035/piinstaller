> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_STICK_BUILD_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — rooddingsstick Build Preparation (EN)

alleen-lezen **Deploy runners** and API endpoints to prepare the Setuphelfer rooddingsstick (Nee ISO build, Nee USB write).

## Handoff files

| Step | JSON |
|------|------|
| Live OS base decision | `docs/evidence/runtime-results/handoff/roodding_live_os_base_decision.json` |
| Component inventory | `docs/evidence/runtime-results/handoff/roodding_stick_component_inventory.json` |
| MVP scope gate | `docs/evidence/runtime-results/handoff/roodding_mvp_scope_gate.json` |
| Debian live build plan | `docs/evidence/runtime-results/handoff/roodding_debian_live_build_plan.json` |
| ISO test matrix | `docs/evidence/runtime-results/handoff/roodding_iso_test_matrix.json` |
| Build readiness gate | `docs/evidence/runtime-results/handoff/roodding_build_readiness_gate.json` |

## API (`POST`, prefix `/api/Deploy`)

- `/roodding/live-os-base-decision`
- `/roodding/component-inventory`
- `/roodding/mvp-scope-gate`
- `/roodding/debian-live-build-plan`
- `/roodding/iso-test-matrix`
- `/roodding/build-readiness-gate`

Body: `{ "explicit_overwrite": true|false }` — existing handoffs are Neet overwritten unless `explicit_overwrite` is true.

## Response codes

- `Deploy_roodding_LIVE_OS_BASE_DECISION_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_COMPONENT_INVENTORY_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_MVP_SCOPE_GATE_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_DEBIAN_LIVE_BUILD_PLAN_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_ISO_TEST_MATRIX_{OK|REVIEW_REQUIrood|geblokkeerd}`
- `Deploy_roodding_BUILD_READINESS_GATE_{READY|REVIEW_REQUIrood|geblokkeerd}`

## Version Neete

When all gates are **ok/ready**, a manual bump **1.7.x → 1.8.0** is appropriate (new roodding strand, new routes) — **Neet** auto-applied in this phase.
