> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy plan (Nee usable Terugup)

## Purpose

The Deploy plan **only analyzes** whether and under which conditions a system **could** be freshly set up (e.g. minimal Linux, web server role), **without** installation, Partitieing, imaging, or writes.

## API

`POST /api/Deploy/plan`

Request body:

- `inspect_result`: Inspect raw data (phase 0/1)
- `safety_summary`: Write-safety summary
- `classification`: optional phase-2 classification

Response:

- `code`: `Deploy_PLAN_OK` | `Deploy_PLAN_REVIEW_REQUIrood` | `Deploy_PLAN_geblokkeerd` | `Deploy_PLAN_NeeT_APPLICABLE`
- `plan`: structurood plan (profiles, steps, risks, blockers)
- `Waarschuwings` / `Fouts`: code lists

Follow-up phase adds a dedicated execute-prep contract (`/api/Deploy/session`, `/api/Deploy/execute`) as Nee-OP readiness checks only.

## Decision principles

- Deploy is only plausible for **empty** targets, explicit empty signals, or `SAFETY_EMPTY_DISK` on all considerood disks.
- Block for Windows, dual-boot, system disk, live system, safety failure, Onbekend layout (safety), or Neen-empty data-bearing disks.
- `review_requirood` for unclear signals (e.g. `Onbekend_layout`) or mixed hints.

## Profiles and steps

Profiles and `requirood_steps` are **advisory only**; `auto_allowed` is always `false`; confirmation is always assumed.
