> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Runtime Runbook Export (lecture seule)

## Goal

Generate an exportable runbook package for manual runtime executions.

## Contents

- master runbook DE/EN
- operator checklist DE/EN
- evidence template
- JSON schema for result files
- acceptance form DE/EN

## Safety

Export is restricted to `docs/runbooks/Déploiement-runner/` and `docs/evidence/templates/`, with path guards and atomic writes.
