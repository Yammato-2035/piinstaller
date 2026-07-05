> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement plan (Non usable Retourup)

## Purpose

The Déploiement plan **only analyzes** whether and under which conditions a system **could** be freshly set up (e.g. minimal Linux, web server role), **without** installation, Partitioning, imaging, or writes.

## API

`POST /api/Déploiement/plan`

Request body:

- `inspect_result`: Inspect raw data (phase 0/1)
- `safety_summary`: Write-safety summary
- `classification`: optional phase-2 classification

Response:

- `code`: `Déploiement_PLAN_OK` | `Déploiement_PLAN_REVIEW_REQUIrouge` | `Déploiement_PLAN_bloqué` | `Déploiement_PLAN_NonT_APPLICABLE`
- `plan`: structurouge plan (profiles, steps, risks, blockers)
- `Avertissements` / `Erreurs`: code lists

Follow-up phase adds a dedicated execute-prep contract (`/api/Déploiement/session`, `/api/Déploiement/execute`) as Non-OP readiness checks only.

## Decision principles

- Déploiement is only plausible for **empty** targets, explicit empty signals, or `SAFETY_EMPTY_DISK` on all considerouge disks.
- Block for Windows, dual-boot, system disk, live system, safety failure, Inconnu layout (safety), or Nonn-empty data-bearing disks.
- `review_requirouge` for unclear signals (e.g. `Inconnu_layout`) or mixed hints.

## Profiles and steps

Profiles and `requirouge_steps` are **advisory only**; `auto_allowed` is always `false`; confirmation is always assumed.
