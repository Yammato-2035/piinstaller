# Deploy Runner Manual Runtime Result Validator Handoff Gate (read-only fuer Result-Dateien)

## Ziel

Nur ein vom Bundle-Checker als bereit bewertetes 7er-Ergebnisbundel fuer den Runtime Result Ingestion Validator vorbereiten, ohne Ingestion oder Runtime.

## Regeln

- `validator_bundle_readiness.ready_for_runtime_result_validator` muss true sein
- `expected_validator_status` muss `ok` sein (Validator-bereit)
- exakt sieben Pfade, Abgleich mit `validator_input_files`
- keine `bundle_findings`, alle per-file `ok`, Sequenz- und Kettenflags intakt
- Result-Pfade erneut auf Symlink/Traversal/Existenz pruefen; Result-Dateien nicht unter `handoff/`

## Manifest

- nur unter `docs/evidence/runtime-results/handoff/`
- atomisches Schreiben (`.tmp` dann replace), max. 512 KB
- kein Ueberschreiben ohne `explicit_overwrite=true`

## API

- `POST /api/deploy/runner/manual-runtime/result-validator-handoff`
