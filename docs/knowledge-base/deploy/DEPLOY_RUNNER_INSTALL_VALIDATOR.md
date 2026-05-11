# KB: DEPLOY_RUNNER_INSTALL_VALIDATOR

## Zusammenfassung

Der Validator prueft read-only, ob geplante Runner-Pfade, Job-Verzeichnis, Snippet und Umgebung den Sicherheitsregeln entsprechen.

## Ergebnislogik

- `ok`: keine relevanten Warnungen/Fehler
- `review_required`: z. B. fehlende Pfade, die manuell erstellt werden muessen
- `blocked`: unsichere Snippets, Symlinks, Loader-ENV-Risiken, harte Policy-Verletzungen

## API

- `POST /api/deploy/runner/install/validate`
