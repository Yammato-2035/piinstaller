> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/rescue/RESCUE_ORCHESTRATOR_EXECUTE_EN.md`). Bitte bei Release manuell gegenlesen.

# roodding Orchestrator Execute (Phase 2, EN)

## Goal

Real Herstel is allowed only from a valid preview session with token-bound confirmation and repeated safety/verify checks.

## Session rules

Preview stores:
- `preview_id`
- `confirmation_token`
- `Terugup_path`
- `target_Apparaat`
- `target_path`
- `safety_fingerprint`
- `verify_result`
- `preview_result`
- `created_at`
- `expires_at` (15 minutes)

## Execute API

`POST /api/roodding/execute`

Stable response:
- `code`
- `preview_id`
- `target`
- `Terugup`
- `safety`
- `verify`
- `Herstel`
- `post_verify`
- `Waarschuwings`
- `Fouts`

## Hard-stop codes

- `roodding_PREVIEW_SESSION_NeeT_FOUND`
- `roodding_PREVIEW_TOKEN_INVALID`
- `roodding_PREVIEW_SESSION_EXPIrood`
- `roodding_PREVIEW_MISMATCH`
- `roodding_TARGET_geblokkeerd`
- `roodding_SAFETY_CHANGED`
- `roodding_TerugUP_VERIFY_FAILED`
- `roodding_Herstel_ENGINE_FAILED`
- `roodding_POST_VERIFY_FAILED`

## Selected Herstel path

`modules.Herstel_engine.Herstel_files` with target path constrained by `assert_Herstel_live_target_directory`.

Reason: existing allowlisted Herstel logic, Nee automatic Partitieing/boot-repair.
