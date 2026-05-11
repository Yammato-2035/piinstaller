# Deploy Runner Lab Acceptance Report Export (read-only)

## Ziel

Export eines zusammenhaengenden Lab-Abnahmeberichts aus bereits aggregierten Acceptance-Daten.

## Output-Pfade

- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md`
- `docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json`
- `docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md`
- `docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md`

## Sicherheit

- nur erlaubte Docs-/Evidence-Roots
- kein Traversal, keine absoluten Fremdpfade, keine Symlinks
- atomisches Schreiben `.tmp -> replace`
- keine Produktionsfreigabe, keine automatische Freigabe

## API

- `POST /api/deploy/runner/lab-readiness/acceptance/export`
