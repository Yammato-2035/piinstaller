# Deploy Runner Routes Decoupling (Phase C.5)

**Erster Slice** — 4 plan-only Routen von direkten Runner-Imports auf `runner_api_facade` umgestellt.

## Warum nur ein kleiner Slice?

- Nach C.6: 104 von 113 direkten Imports verbleiben (Execute, Rescue, Write, Operator-Pfade)
- C.4 verbietet `allowed_to_execute` — keine Execute-Freigabe
- Response-Kompatibilität nur bei plan-only Gate sicher

## Facade-Hilfen (neu)

- `build_plan_only_response(runner_id)`
- `build_readonly_runner_response(runner_id)`
- `assert_runner_plan_allowed(runner_id)`

## Migrierte Routen

`POST /runner/next-phase/gate`, `/version-governance/state`, `/version-source-of-truth-check`, `/legacy-identifier-inventory`

## C.6 (erledigt)

5 Evidence/Identifier-Routen decoupled — siehe `DEPLOY_RUNNER_ROUTES_DECOUPLING_C6.md`. Imports 109→104.

## C.7

Nächster Slice nach `allowed_plan_only`-Liste; Execute-Gate bleibt Zukunftsthema.
