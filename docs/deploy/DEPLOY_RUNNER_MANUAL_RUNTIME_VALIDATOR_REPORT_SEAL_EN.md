# Validator Report Seal (read-only + seal write)

- Input: `validator_dryrun_report.json` under `handoff/`
- Output: `validator_dryrun_report.seal.json` (SHA256 over raw report bytes only)
- Does not modify the dry-run report or runtime result files

API: `POST /api/deploy/runner/manual-runtime/result-validator-report-seal`

i18n: `docs/i18n/validator_report_seal_DE.json`, `validator_report_seal_EN.json`
