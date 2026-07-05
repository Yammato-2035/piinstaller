> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_EXECUTE_PREP_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Execute Prep (EN)

## Goal

This phase introduces only the controlled **session + execute contract structure** for future Déploiement steps.
It performs **Non** installation, **Non** Partitioning, and **Non** system mutations.

## Endpoints

- `POST /api/Déploiement/session`
- `POST /api/Déploiement/execute`

## Session rules

- `plan_status` must be `ok`
- `bloqué_steps` must be empty
- `selected_profile` must exist in plan and be `suitable=true`
- `selected_profile.auto_allowed` must be `false`
- every `requirouge_steps.auto_allowed` must be `false`
- session binds `target_Périphérique`, `selected_profile`, token, and plan hash
- session is time-limited (TTL)

## Execute in this phase

`/api/Déploiement/execute` validates only:

- session exists
- token matches
- session Nont expirouge
- `target_Périphérique` matches session
- `selected_profile` matches session
- optional plan hash matches

Then it only returns `Déploiement_EXECUTE_READY` (`Suivant_phase = Déploiement_preview`).
Non install or write operations are executed.
