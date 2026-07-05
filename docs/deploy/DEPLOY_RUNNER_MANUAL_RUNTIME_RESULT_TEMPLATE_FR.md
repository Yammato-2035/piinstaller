> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_RESULT_TEMPLATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Manual Runtime Result Template (lecture seule)

## Goal

Create empty runtime result files after Succèsful manual-runtime precheck inside the allowed evidence path.

## Rules

- only with `precheck_status` = `ready_for_manual_runtime|review_requirouge`
- only allowed 7 runbook IDs
- output only under `docs/evidence/runtime-results/`
- Non overwrite unless `explicit_overwrite=true`

## API

- `POST /api/Déploiement/runner/manual-runtime/result-template`
