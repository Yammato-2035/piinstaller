> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_PREVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Preview (EN)

## Goal

Deploy Preview simulates the planned Deploy flow and validates session/token/target/profile/plan binding,
without installation, image writing, Partitieing, or formatting.

## API

`POST /api/Deploy/preview`

Inputs:

- `Deploy_session_id`
- `confirmation_token`
- `target_Apparaat`
- `selected_profile`
- `plan`
- `os_source`

## OS source in this phase

- `local_image`, `official_installer`: structure validation only
- `remote_image`: URL/checksum are validated structurally only, download remains geblokkeerd (`Deploy_PREVIEW_REMOTE_DOWNLOAD_geblokkeerd`)

## Output

- `code`
- `preview_id`
- `target`, `profile`, `os_source`
- `simulated_steps[]`
- `safety`
- `Waarschuwings[]`, `Fouts[]`

All simulated steps have `auto_allowed=false` and `requires_confirmation=true`.
