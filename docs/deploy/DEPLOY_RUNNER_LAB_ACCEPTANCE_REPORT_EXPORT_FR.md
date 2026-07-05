> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_LAB_ACCEPTANCE_REPORT_EXPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Lab Acceptance Report Export (lecture seule)

## Goal

Export a coherent lab acceptance report from already aggregated acceptance data.

## Output Paths

- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json`
- `docs/runbooks/Déploiement-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md`
- `docs/runbooks/Déploiement-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md`

## Safety

- only allowed docs/evidence roots
- Non traversal, Non absolute foreign paths, Non symlink targets
- atomic write `.tmp -> replace`
- Non production approval claim, Non automatic approval

## API

- `POST /api/Déploiement/runner/lab-readiness/acceptance/export`
