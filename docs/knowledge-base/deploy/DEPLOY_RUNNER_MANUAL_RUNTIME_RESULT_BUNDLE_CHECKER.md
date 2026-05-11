# KB: DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECKER

## Ueberblick

Read-only Bundle-Vorpruefung fuer das komplette Set manueller Runtime-Ergebnisdateien unter `docs/evidence/runtime-results/`.

## Warum

Die Ingestion prueft Sequenz und Abhaengigkeiten; der Bundle-Checker fasst alle Dateien zusammen und liefert frueh konsistente Bundle-Findings.

## API

- `POST /api/deploy/runner/manual-runtime/result-bundle-check`
