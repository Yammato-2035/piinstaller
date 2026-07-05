> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_REPORT_SEAL_EN.md`). Bitte bei Release manuell gegenlesen.

# Validator Report Seal (lecture seule + seal write)

- Input: `validator_dryrun_report.json` under `handoff/`
- Output: `validator_dryrun_report.seal.json` (SHA256 over raw report bytes only)
- Does Nont modify the dry-run report or runtime result files

API: `POST /api/Déploiement/runner/manual-runtime/result-validator-report-seal`

i18n: `docs/i18n/validator_report_seal_DE.json`, `validator_report_seal_EN.json`
