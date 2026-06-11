# Deploy Runner Routes Decoupling (Phase C.5)

**First slice** — 4 plan-only routes moved from direct runner imports to `runner_api_facade`.

## Why only a small slice?

- 109 of 113 direct imports remain (execute, rescue, write, operator paths)
- C.4 forbids `allowed_to_execute` — no execute release
- Response compatibility only safe for plan-only gate

## New facade helpers

- `build_plan_only_response(runner_id)`
- `build_readonly_runner_response(runner_id)`
- `assert_runner_plan_allowed(runner_id)`

## Migrated routes

`POST /runner/next-phase/gate`, `/version-governance/state`, `/version-source-of-truth-check`, `/legacy-identifier-inventory`

## C.6 / C.7

Further slices from `allowed_plan_only` list; execute gate remains a future topic after full migration.
