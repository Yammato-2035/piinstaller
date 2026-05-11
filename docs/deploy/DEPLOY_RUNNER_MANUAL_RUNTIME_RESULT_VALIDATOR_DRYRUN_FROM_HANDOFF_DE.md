# Deploy Runner Manual Runtime Result Validator Dry-Run from Handoff (read-only)

## Ziel

Den bestehenden Runtime Result Ingestion Validator ausschliesslich gegen das Handoff-Manifest ausfuehren: nur lesen, pruefen, Dryrun-Bericht schreiben.

## Ablauf

- Manifest unter `docs/evidence/runtime-results/handoff/` validieren (Pfad, Groesse, JSON, genau sieben `validator_input_files`)
- Result-Pfade erneut pruefen (nicht unter `handoff/`, existent, max. 2 MB)
- `validate_runner_runtime_result_bundle(..., acceptance_decision="blocked")` aufrufen (keine Ingestion)
- Bericht nach `docs/evidence/runtime-results/handoff/validator_dryrun_report.json` (atomisch, max. Ueberschreiben nur mit `explicit_overwrite`)

## API

- `POST /api/deploy/runner/manual-runtime/result-validator-dryrun-from-handoff`
