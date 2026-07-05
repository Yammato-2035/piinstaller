> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_BUNDLE_CHECKER_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Manual Runtime Result Bundle Checker (alleen-lezen)

## Purpose

Validate all seven runtime result JSON files together before handing them to the runtime result ingestion validator.

## Output

- Runbook sequence (all seven, correct order, Nee duplicates)
- Per file: Intern use of the edit checker
- Bundle-level safety findings (`BUNDLE_*`)
- `validator_bundle_readiness` with Nee automatic approval

## API

- `POST /api/Deploy/runner/manual-runtime/result-bundle-check`
