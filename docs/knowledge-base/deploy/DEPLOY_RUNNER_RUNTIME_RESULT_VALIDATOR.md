# KB: DEPLOY_RUNNER_RUNTIME_RESULT_VALIDATOR

## Ueberblick

Read-only Ingestion-Validator fuer manuell erzeugte Runtime-Ergebnisdateien.

## Warum

Ergebnisdateien muessen konsistent und sicher auswertbar sein, bevor eine manuelle Lab-Abnahmeentscheidung getroffen wird.

## Regeln

- erlaubter Pfad: `docs/evidence/runtime-results/`
- nur `.json`, keine Symlinks, kein Traversal
- Pflichtfelder/Sequence/Evidence fail-closed
- keine automatische Freigabe durch `lab_ready_candidate`

## API

- `POST /api/deploy/runner/runtime-results/validate`
