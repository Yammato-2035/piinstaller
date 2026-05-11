# KB: DEPLOY_RUNNER_ROLLBACK_RUNTIME_TEST_PLAN

## Ueberblick

Read-only Testdesign fuer den Gap `RUNNER_GAP_ROLLBACK_RUNTIME_OPEN`.

## Leitlinie

Rollback bleibt strikt auf erlaubte Testartefakte begrenzt; keine Systempfad-Loeschungen, kein Audit-Loeschen.

## API

- `POST /api/deploy/runner/rollback-runtime/test-plan`
