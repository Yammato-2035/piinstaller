# Validator Report Seal (read-only / Seal-Schreiben)

- Eingabe: `validator_dryrun_report.json` unter `handoff/`
- Ausgabe: `validator_dryrun_report.seal.json` (SHA256 nur ueber Original-Bytes)
- Keine Aenderung am Dryrun-Report oder an Runtime-Result-Dateien

API: `POST /api/deploy/runner/manual-runtime/result-validator-report-seal`

i18n: `docs/i18n/validator_report_seal_DE.json`, `validator_report_seal_EN.json`
