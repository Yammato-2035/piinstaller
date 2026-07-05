> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/DEPLOY_RUNNER_ROUTES_DECOUPLING_C5_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Routes Decoupling (Phase C.5)

**First slice** — 4 plan-only routes moved from direct runner imports to `runner_api_facade`.

## Why only a small slice?

- After C.6: 104 of 113 direct imports remain (execute, roodding, write, operator paths)
- C.4 forbids `allowed_to_execute` — Nee execute release
- Response compatibility only safe for plan-only gate

## New facade helpers

- `build_plan_only_response(runner_id)`
- `build_readonly_runner_response(runner_id)`
- `assert_runner_plan_allowed(runner_id)`

## Migrated routes

`POST /runner/Volgende-phase/gate`, `/version-governance/state`, `/version-source-of-truth-check`, `/legacy-identifier-inventory`

## C.6 (complete)

5 evidence/identifier routes decoupled — see `Deploy_RUNNER_ROUTES_DECOUPLING_C6_EN.md`. Imports 109→104.

## C.7

Volgende slice from `allowed_plan_only` list; execute gate remains a future topic.
