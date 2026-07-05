> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_PREVIEW_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Preview (EN)

## Goal

Déploiement Preview simulates the planned Déploiement flow and validates session/token/target/profile/plan binding,
without installation, image writing, Partitioning, or formatting.

## API

`POST /api/Déploiement/preview`

Inputs:

- `Déploiement_session_id`
- `confirmation_token`
- `target_Périphérique`
- `selected_profile`
- `plan`
- `os_source`

## OS source in this phase

- `local_image`, `official_installer`: structure validation only
- `remote_image`: URL/checksum are validated structurally only, download remains bloqué (`Déploiement_PREVIEW_REMOTE_DOWNLOAD_bloqué`)

## Output

- `code`
- `preview_id`
- `target`, `profile`, `os_source`
- `simulated_steps[]`
- `safety`
- `Avertissements[]`, `Erreurs[]`

All simulated steps have `auto_allowed=false` and `requires_confirmation=true`.
