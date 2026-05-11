# KB: DEPLOY_RUNNER_MANUAL_RUNTIME_PRECHECK

## Ueberblick

Read-only Precheck fuer die zulaessige Folgephase `NEXT_PHASE_MANUAL_RUNTIME_TESTS`.

## Kernaussage

Der Precheck ersetzt keine Ausfuehrung, sondern bewertet nur Startbereitschaft, Operator-Flags, Testmedien-Kontext und Evidence-Plan.

## API

- `POST /api/deploy/runner/manual-runtime/precheck`
