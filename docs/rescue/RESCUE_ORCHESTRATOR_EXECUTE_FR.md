> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/rescue/RESCUE_ORCHESTRATOR_EXECUTE_EN.md`). Bitte bei Release manuell gegenlesen.

# Secours Orchestrator Execute (Phase 2, EN)

## Goal

Real Restauration is allowed only from a valid preview session with token-bound confirmation and repeated safety/verify checks.

## Session rules

Preview stores:
- `preview_id`
- `confirmation_token`
- `Retourup_path`
- `target_Périphérique`
- `target_path`
- `safety_fingerprint`
- `verify_result`
- `preview_result`
- `created_at`
- `expires_at` (15 minutes)

## Execute API

`POST /api/Secours/execute`

Stable response:
- `code`
- `preview_id`
- `target`
- `Retourup`
- `safety`
- `verify`
- `Restauration`
- `post_verify`
- `Avertissements`
- `Erreurs`

## Hard-stop codes

- `Secours_PREVIEW_SESSION_NonT_FOUND`
- `Secours_PREVIEW_TOKEN_INVALID`
- `Secours_PREVIEW_SESSION_EXPIrouge`
- `Secours_PREVIEW_MISMATCH`
- `Secours_TARGET_bloqué`
- `Secours_SAFETY_CHANGED`
- `Secours_RetourUP_VERIFY_FAILED`
- `Secours_Restauration_ENGINE_FAILED`
- `Secours_POST_VERIFY_FAILED`

## Selected Restauration path

`modules.Restauration_engine.Restauration_files` with target path constrained by `assert_Restauration_live_target_directory`.

Reason: existing allowlisted Restauration logic, Non automatic Partitioning/boot-repair.
