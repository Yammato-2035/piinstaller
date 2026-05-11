# Deploy Execute Prep (EN)

## Goal

This phase introduces only the controlled **session + execute contract structure** for future deploy steps.
It performs **no** installation, **no** partitioning, and **no** system mutations.

## Endpoints

- `POST /api/deploy/session`
- `POST /api/deploy/execute`

## Session rules

- `plan_status` must be `ok`
- `blocked_steps` must be empty
- `selected_profile` must exist in plan and be `suitable=true`
- `selected_profile.auto_allowed` must be `false`
- every `required_steps.auto_allowed` must be `false`
- session binds `target_device`, `selected_profile`, token, and plan hash
- session is time-limited (TTL)

## Execute in this phase

`/api/deploy/execute` validates only:

- session exists
- token matches
- session not expired
- `target_device` matches session
- `selected_profile` matches session
- optional plan hash matches

Then it only returns `DEPLOY_EXECUTE_READY` (`next_phase = deploy_preview`).
No install or write operations are executed.
