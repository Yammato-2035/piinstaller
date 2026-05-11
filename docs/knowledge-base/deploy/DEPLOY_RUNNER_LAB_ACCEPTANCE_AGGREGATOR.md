# KB: DEPLOY_RUNNER_LAB_ACCEPTANCE_AGGREGATOR

## Ueberblick

Read-only Aggregator fuer die manuelle Lab-Abnahme auf Basis bereits validierter Runtime-Ergebnisdateien.

## Kernpunkte

- bewertet 7 Pflicht-Runbooks konsistent
- liefert `runbook_outcomes`, `evidence_summary` und `residual_risks`
- verhindert jede automatische Produktionsfreigabe

## API

- `POST /api/deploy/runner/lab-readiness/acceptance`
