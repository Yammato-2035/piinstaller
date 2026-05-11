# KB: DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE

## Ueberblick

Read-only Generator fuer manuell zu befuellende Runtime-Ergebnisdateien.

## Sicherheit

- harter Pfadschutz auf `docs/evidence/runtime-results/`
- fail-closed bei unbekanntem Runbook oder ungueltigem Precheck
- kein automatisches Befuellen oder Starten von Runtime-Ausfuehrung

## API

- `POST /api/deploy/runner/manual-runtime/result-template`
