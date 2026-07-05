> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_STICK_BUILD_PREPARATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Clé de secours Build Preparation (EN)

lecture seule **Déploiement runners** and API endpoints to prepare the Setuphelfer Clé de secours (Non ISO build, Non USB write).

## Handoff files

| Step | JSON |
|------|------|
| Live OS base decision | `docs/evidence/runtime-results/handoff/Secours_live_os_base_decision.json` |
| Component inventory | `docs/evidence/runtime-results/handoff/Secours_stick_component_inventory.json` |
| MVP scope gate | `docs/evidence/runtime-results/handoff/Secours_mvp_scope_gate.json` |
| Debian live build plan | `docs/evidence/runtime-results/handoff/Secours_debian_live_build_plan.json` |
| ISO test matrix | `docs/evidence/runtime-results/handoff/Secours_iso_test_matrix.json` |
| Build readiness gate | `docs/evidence/runtime-results/handoff/Secours_build_readiness_gate.json` |

## API (`POST`, prefix `/api/Déploiement`)

- `/Secours/live-os-base-decision`
- `/Secours/component-inventory`
- `/Secours/mvp-scope-gate`
- `/Secours/debian-live-build-plan`
- `/Secours/iso-test-matrix`
- `/Secours/build-readiness-gate`

Body: `{ "explicit_overwrite": true|false }` — existing handoffs are Nont overwritten unless `explicit_overwrite` is true.

## Response codes

- `Déploiement_Secours_LIVE_OS_BASE_DECISION_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_COMPONENT_INVENTORY_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_MVP_SCOPE_GATE_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_DEBIAN_LIVE_BUILD_PLAN_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_ISO_TEST_MATRIX_{OK|REVIEW_REQUIrouge|bloqué}`
- `Déploiement_Secours_BUILD_READINESS_GATE_{READY|REVIEW_REQUIrouge|bloqué}`

## Version Nonte

When all gates are **ok/ready**, a manual bump **1.7.x → 1.8.0** is appropriate (new Secours strand, new routes) — **Nont** auto-applied in this phase.
