# Deploy plan (no usable backup)

## Purpose

The deploy plan **only analyzes** whether and under which conditions a system **could** be freshly set up (e.g. minimal Linux, web server role), **without** installation, partitioning, imaging, or writes.

## API

`POST /api/deploy/plan`

Request body:

- `inspect_result`: Inspect raw data (phase 0/1)
- `safety_summary`: Write-safety summary
- `classification`: optional phase-2 classification

Response:

- `code`: `DEPLOY_PLAN_OK` | `DEPLOY_PLAN_REVIEW_REQUIRED` | `DEPLOY_PLAN_BLOCKED` | `DEPLOY_PLAN_NOT_APPLICABLE`
- `plan`: structured plan (profiles, steps, risks, blockers)
- `warnings` / `errors`: code lists

Follow-up phase adds a dedicated execute-prep contract (`/api/deploy/session`, `/api/deploy/execute`) as NO-OP readiness checks only.

## Decision principles

- Deploy is only plausible for **empty** targets, explicit empty signals, or `SAFETY_EMPTY_DISK` on all considered disks.
- Block for Windows, dual-boot, system disk, live system, safety failure, unknown layout (safety), or non-empty data-bearing disks.
- `review_required` for unclear signals (e.g. `unknown_layout`) or mixed hints.

## Profiles and steps

Profiles and `required_steps` are **advisory only**; `auto_allowed` is always `false`; confirmation is always assumed.
