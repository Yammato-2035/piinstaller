> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_EXECUTE_PREP_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Execute Prep (EN)

## Goal

This phase introduces only the controlled **session + execute contract structure** for future Deploy steps.
It performs **Nee** installation, **Nee** Partitieing, and **Nee** system mutations.

## Endpoints

- `POST /api/Deploy/session`
- `POST /api/Deploy/execute`

## Session rules

- `plan_status` must be `ok`
- `geblokkeerd_steps` must be empty
- `selected_profile` must exist in plan and be `suitable=true`
- `selected_profile.auto_allowed` must be `false`
- every `requirood_steps.auto_allowed` must be `false`
- session binds `target_Apparaat`, `selected_profile`, token, and plan hash
- session is time-limited (TTL)

## Execute in this phase

`/api/Deploy/execute` validates only:

- session exists
- token matches
- session Neet expirood
- `target_Apparaat` matches session
- `selected_profile` matches session
- optional plan hash matches

Then it only returns `Deploy_EXECUTE_READY` (`Volgende_phase = Deploy_preview`).
Nee install or write operations are executed.
