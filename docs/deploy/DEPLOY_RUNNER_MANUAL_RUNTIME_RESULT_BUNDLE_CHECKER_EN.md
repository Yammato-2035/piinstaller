# Deploy Runner Manual Runtime Result Bundle Checker (read-only)

## Purpose

Validate all seven runtime result JSON files together before handing them to the runtime result ingestion validator.

## Output

- Runbook sequence (all seven, correct order, no duplicates)
- Per file: internal use of the edit checker
- Bundle-level safety findings (`BUNDLE_*`)
- `validator_bundle_readiness` with no automatic approval

## API

- `POST /api/deploy/runner/manual-runtime/result-bundle-check`
