# Deploy Runner Lab Acceptance Report Export (read-only)

## Goal

Export a coherent lab acceptance report from already aggregated acceptance data.

## Output Paths

- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json`
- `docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md`
- `docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md`

## Safety

- only allowed docs/evidence roots
- no traversal, no absolute foreign paths, no symlink targets
- atomic write `.tmp -> replace`
- no production approval claim, no automatic approval

## API

- `POST /api/deploy/runner/lab-readiness/acceptance/export`
