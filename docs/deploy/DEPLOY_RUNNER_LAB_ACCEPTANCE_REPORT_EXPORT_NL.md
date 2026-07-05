> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_REPORT_EXPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Lab Acceptance Report Export (alleen-lezen)

## Goal

Export a coherent lab acceptance report from already aggregated acceptance data.

## Output Paths

- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json`
- `docs/runbooks/Deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md`
- `docs/runbooks/Deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md`

## Safety

- only allowed docs/evidence roots
- Nee traversal, Nee absolute foreign paths, Nee symlink targets
- atomic write `.tmp -> replace`
- Nee production approval claim, Nee automatic approval

## API

- `POST /api/Deploy/runner/lab-readiness/acceptance/export`
