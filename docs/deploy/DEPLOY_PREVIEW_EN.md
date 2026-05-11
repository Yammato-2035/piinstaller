# Deploy Preview (EN)

## Goal

Deploy Preview simulates the planned deploy flow and validates session/token/target/profile/plan binding,
without installation, image writing, partitioning, or formatting.

## API

`POST /api/deploy/preview`

Inputs:

- `deploy_session_id`
- `confirmation_token`
- `target_device`
- `selected_profile`
- `plan`
- `os_source`

## OS source in this phase

- `local_image`, `official_installer`: structure validation only
- `remote_image`: URL/checksum are validated structurally only, download remains blocked (`DEPLOY_PREVIEW_REMOTE_DOWNLOAD_BLOCKED`)

## Output

- `code`
- `preview_id`
- `target`, `profile`, `os_source`
- `simulated_steps[]`
- `safety`
- `warnings[]`, `errors[]`

All simulated steps have `auto_allowed=false` and `requires_confirmation=true`.
