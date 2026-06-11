# Deploy Runner Routes Decoupling (Phase C.5)

**Erster Slice** — 4 plan-only Routen von direkten Runner-Imports auf `runner_api_facade` umgestellt.

## Warum nur ein kleiner Slice?

- 109 von 113 direkten Imports bleiben (Execute, Rescue, Write, Operator-Pfade)
- C.4 verbietet `allowed_to_execute` — keine Execute-Freigabe
- Response-Kompatibilität nur bei plan-only Gate sicher

## Facade-Hilfen (neu)

- `build_plan_only_response(runner_id)`
- `build_readonly_runner_response(runner_id)`
- `assert_runner_plan_allowed(runner_id)`

## Migrierte Routen

`POST /runner/next-phase/gate`, `/version-governance/state`, `/version-source-of-truth-check`, `/legacy-identifier-inventory`

## C.6 / C.7

Weitere Slices nach `allowed_plan_only`-Liste; Execute-Gate bleibt Zukunftsthema nach vollständiger Migration.
