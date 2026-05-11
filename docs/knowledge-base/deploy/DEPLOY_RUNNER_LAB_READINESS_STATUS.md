# KB: DEPLOY_RUNNER_LAB_READINESS_STATUS

## Ueberblick

Read-only Statusmodell zur Trennung von abgeschlossenem Testdesign und weiterhin offener Runtime-Ausfuehrung.

## Ergebnis

- `lab_readiness_status` kann nur `test_design_ready|runtime_blocked|review_required` sein
- Runtime-Gaps bleiben offen, bis manuelle Runtime-Evidence vorliegt

## API

- `POST /api/deploy/runner/lab-readiness/status`
