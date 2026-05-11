# Deploy Runner Lab Acceptance Aggregator (read-only)

## Ziel

Validierte Runtime-Ergebnisse zentral aggregieren und einen Lab-Abnahmestatus ableiten.

## Status-Regeln

- `lab_ready_candidate`: nur bei Validator `ok`, 7/7 Runbooks vorhanden, 7/7 `pass`, keine Blocking-Findings
- `repeat_required`: bei Teilwiederholungen, partieller Evidence, offener Operatorentscheidung
- `blocked`: bei Sicherheitsfinding, fehlgeschlagener Sequenz, fehlendem Rollback oder widerspruechlicher Entscheidung

## Sicherheit

- rein read-only Aggregation bereits validierter Daten
- keine automatische Freigabe
- `operator_decision_required` bleibt immer `true`

## API

- `POST /api/deploy/runner/lab-readiness/acceptance`
